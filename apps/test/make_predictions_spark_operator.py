"""
This script performs the same operations as the 'make_predictions.py' but this one is supposed to be run using Spark Operator. Spark Operator will
create driver and executor pods which will save model's predictions in the Iceberg catalog.

For running this code we need to prepare the following environment variables first, which will be used to prepare configs for Spark:
    - STORAGE_ACCOUNT, CONTAINER - Name of the Azure Storage Account and container used as an Iceberg catalog (data warehouse)
    - SA_ACCESS_KEY - Access key to the Storage Account used
    - CATALOG_FOLDER - Folder in the Storage Account container used as an Iceberg catalog (to store all the data)

We need to provide Spark configuration in this script as there is a problem with providing dynamic values for those configurations (e.g. from secrets)
in the spark-defaults.conf file or in the SparkApplication CRD when using Spark Operator.
"""

import os, sys, pathlib

# Add "apps" folder to the sys.path so we can import from "apps/common"
sys.path.append(str(pathlib.Path(__file__).parent.parent.resolve()))

from common.spark_thrift_class import SparkThrift
from common.spark import create_session, prepare_iceberg_configs
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
model = mlflow.pyfunc.load_model("models:/linear_regression_revenue/Production")

# Load data about clients for which we will make predictions
clients = spark_thrift.read_query("select clientID, month from dwh_fact.customers_total_revenue;")

# Make predictions with the model
predictions = model.predict(clients)

# Prepare a 2D array called 'predictions' of the format:
    # [
    #     [client_id_1, month_1, prediction]
    #     ,[client_id_2, month_2, prediction]
    #     ...
    # ]
# To save it in the Iceberg table
# client_ids = clients['clientID'].values
# client_ids = np.array(client_ids).reshape(len(client_ids), 1)
predictions = np.array(predictions).reshape(len(predictions), 1)

# print('client_ids: ', client_ids)
# print('predictions: ', predictions)

predictions = np.concatenate((clients.values, predictions), axis = 1)
# print('predictions: ', predictions)


# Prepare configs needed to work with Spark and Iceberg. The prepare_iceberg_configs function requires to prepare the following environment variables first:
#   - STORAGE_ACCOUNT, CONTAINER - Name of the Azure Storage Account and container used as an Iceberg catalog (data warehouse)
#   - SA_ACCESS_KEY - Access key to the Storage Account used
#   - CATALOG_FOLDER - Folder in the Storage Account container used as an Iceberg catalog (to store all the data)
spark_configs = prepare_iceberg_configs()

# Create SparkSession using configs prepared previously. It will be used to save data in Iceberg catalog.
spark = create_session(app_name="write_iceberg", configs=spark_configs)

spark_df = spark.createDataFrame(predictions, schema=['clientID', 'month', 'predictedRevenue'])

# We create a table if it doesn't exist yet and then overwrite it. If we try to use only createOrReplace without creating this table earlier, 
# it gives an error that it can't find the metadata/version-hint.text file even though it does exist. Probably it is about some delay, the file
# exists but Spark still for some time can't see it.

# Create the Iceberg table if it doesn't exist yet
spark_thrift.run_query("""
CREATE TABLE IF NOT EXISTS dwh_fact.client_total_revenue_predictions (
    clientID INT
    ,month date
    ,predictedRevenue int
)
USING ICEBERG
""")

# Add records to the Iceberg table (overwrite the existing table). 
spark_df.writeTo("dwh_fact.client_total_revenue_predictions").overwritePartitions()