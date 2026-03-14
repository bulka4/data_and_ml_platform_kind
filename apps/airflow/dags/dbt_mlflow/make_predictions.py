"""
Make predictions and save them in Iceberg catalog.
"""

import sys, pathlib

# Add "apps" folder to the sys.path so we can import from "apps/common"
sys.path.append(str(pathlib.Path(__file__).parent.parent.parent.parent.resolve()))

from common.spark_class import Spark
from pyspark.sql import SparkSession
import mlflow
import mlflow.pyfunc
import numpy as np

# Connect to the Spark Thrift Server (Kubernetes pod) for reading data from Iceberg catalog
spark_thrift = Spark(
    # Spark Kubernetes pod has a DNS name of the format: <service-name>.<namespace>.svc
    host='spark-thrift-server.spark.svc'
    ,port=10000
    ,auth='NONE'
)

# Start a new Spark Session for saving data in Iceberg catalog. Use Kubernetes as a resource manager (master) to start a new Spark dirver.
# We don't use here Spark Thrift Server driver and we need to provide the same Spark configuration as for the Thrift Server.
spark = SparkSession.builder \
    .appName("write_iceberg") \
    .master("k8s://https://kubernetes.default.svc") \
    .getOrCreate()

# Load model from MLflow
model = mlflow.pyfunc.load_model("models:/linear_regression_revenue/Production")

# Load data about clients for which we will make predictions
clients = spark_thrift.read_query("select clientID from dwh_dim.clients;")
# clients = spark.run_query("drop table dwh_fact.customers_total_tevenue;")

# print('clients: ', clients)

predictions = model.predict(clients)

predictions = np.concatenate((clients['clientID'].values, predictions), axis = 1)
print('predictions: ', predictions)

spark_df = spark.createDataFrame(predictions)
spark_df.writeTo("dwh_fact.client_total_revenue_predictions").append()