"""
This script performs the same operations as the 'make_predictions.py' but this one is supposed to be run using Spark Operator. Spark Operator will
create driver and executor pods which will save model's predictions in the Iceberg catalog.

Before we run this script we need to:
    - Prepare the following environment variables first, which will be used to prepare configs for Spark:
        - STORAGE_ACCOUNT, CONTAINER - Name of the Azure Storage Account and container used as an Iceberg catalog (data warehouse)
        - SA_ACCESS_KEY - Access key to the Storage Account used
        - CATALOG_FOLDER - Folder in the Storage Account container used as an Iceberg catalog (to store all the data)
    - Create the dwh_fact.clients_total_revenue_predictions table using dbt, so this table is managed by dbt and this script
        only populates it with data.

We need to provide Spark configuration in this script as there is a problem with providing dynamic values for those configurations (e.g. from secrets)
in the spark-defaults.conf file or in the SparkApplication CRD when using Spark Operator.
"""

import os, sys, pathlib

# Add "apps" folder to the sys.path so we can import from "apps/common"
sys.path.append(str(pathlib.Path(__file__).parent.parent.parent.parent.resolve()))

from common.spark_thrift_class import SparkThrift
from common.spark import create_session, prepare_iceberg_configs
from pyspark.sql.functions import to_date, concat, lit, lpad, col
import mlflow
import mlflow.pyfunc
import numpy as np



# DNS name of the Spark Thrift Server
spark_thrift_dns = os.environ['SPARK_THRIFT_SERVER_DNS']

# Connect to the Spark Thrift Server (Kubernetes pod) for reading data from Iceberg catalog
spark_thrift = SparkThrift(
    # Spark Kubernetes pod has a DNS name of the format: <service-name>.<namespace>.svc
    host=spark_thrift_dns
    ,port=10000
    ,auth='NONE'
)

# Load model from MLflow registry (saved by the promote_model.py script)
model_name = 'linear_regression_revenue'
model_stage = 'Production'
model = mlflow.pyfunc.load_model(f"models:/{model_name}/{model_stage}")

# Get model URI with the version (that's a unique identifier of the model which will save in the target table with predictions, to indicate that
# this model was used)
model_info = mlflow.MlflowClient().get_latest_versions(
    name=model_name,
    stages=[model_stage]
)[0]
model_uri = f'models:/{model_name}/{model_info.version}'

# Create the table where we will save predictions if it doesn't exist yet
spark_thrift.run_query(
    """
    CREATE TABLE IF NOT EXISTS dwh_fact.clients_total_revenue_predictions (
        clientID int
        ,month date
        ,predictedRevenue float
        ,modelURI string
    )
    USING ICEBERG
    """
)

# Load data about clients and months for which we will make predictions (load only those recprds for which we didn't make predictions yet)
clients = spark_thrift.read_query(
    query="""
    SELECT
        rev.clientID
        ,add_months(rev.month, 1) as nextMonth  -- next month for which predictions will be made
        ,rev.revenue as revenueLastMonth        -- last month revenue based on which we make predictions
    FROM
        dwh_fact.clients_total_revenue AS rev

        LEFT JOIN dwh_fact.clients_total_revenue_predictions AS pred
            ON pred.clientID = rev.clientID
            AND pred.month = add_months(rev.month, 1)
    WHERE
        pred.clientID IS NULL
    """
    ,date_columns=['nextMonth'] # columns to convert into the datetime type
)

print(clients.dtypes)

# Make predictions with the model
predictions = model.predict(clients[['clientID', 'revenueLastMonth']])

# Prepare a 2D array called 'predictions' to save it in the Iceberg table. 
# It has columns: 
#   - clientID - Input for a model
#   - nextMonth - Month for which we made predictions
#   - predictedRevenueNextMonth - Predicted revenue for the next month
# predictions = np.array(predictions).reshape(len(predictions), 1)
# predictions = np.concatenate((clients[['clientID', 'nextMonth']].values, predictions), axis = 1)

# Add a column with predictions
clients['predictedRevenue'] = predictions

# Prepare configs needed to work with Spark and Iceberg. The prepare_iceberg_configs function requires to prepare the following environment variables first:
#   - STORAGE_ACCOUNT, CONTAINER - Name of the Azure Storage Account and container used as an Iceberg catalog (data warehouse)
#   - SA_ACCESS_KEY - Access key to the Storage Account used
#   - CATALOG_FOLDER - Folder in the Storage Account container used as an Iceberg catalog (to store all the data)
spark_configs = prepare_iceberg_configs()

# Create SparkSession using configs prepared previously. It will be used to save data in Iceberg catalog.
spark = create_session(app_name="write_iceberg", configs=spark_configs)

spark_df = spark.createDataFrame(
    clients[['clientID', 'nextMonth', 'predictedRevenue']]
    ,schema=['clientID', 'month', 'predictedRevenue']
)

print(clients)
spark_df.show()

# Create a date and model_uri columns
spark_df = spark_df.withColumn('modelURI', lit(model_uri))

# Add records to the Iceberg table. 
spark_df.writeTo("dwh_fact.clients_total_revenue_predictions").append()