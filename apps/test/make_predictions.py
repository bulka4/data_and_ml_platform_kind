"""
This is a script for testing. It is the best to use it in the pod created using the "helm_charts/development_pods/mlflow" Helm chart.

This script:
    - Loads data (to make predictions for) from the Iceberg catalog using PyHive and by connecting to the Spark Thrift Server
    - Loads a model from MLflow registry
    - Makes predictions with it
    - Saves predictions in the Iceberg catalog using Spark (we run Spark here in a client mode, creating a new driver. We don't use fro that
        the Thrift server).
"""

import os, sys, pathlib

# Add "apps" folder to the sys.path so we can import from "apps/common"
sys.path.append(str(pathlib.Path(__file__).parent.parent.parent.parent.resolve()))

from common.spark_thrift_class import SparkThrift
from pyspark.sql import SparkSession
import mlflow
import mlflow.pyfunc
import numpy as np

# =============== Configuration ===============

# Parameters for Spark:
#   - namespace - Kubernetes namespace where to create executor pods
#   - instances - How many executors to create
#   - container.image - Image to use for driver and executor pods
#   - driver_host - DNS name of the Spark driver which will be used by executor pods to talk to the driver. Since we run here
#           Spark in the client mode, then driver will run in the pod where we run this script, so driver_host should be
#           the DNS name of that pod (i.e. "{service-name}.{namespace}.svc", where "service-name" is the name of the service that pod uses)
namespace = "mlflow"
instances = 1
container_image = "mlflow-spark:latest"
driver_host = f"dev-pod.{namespace}.svc.cluster.local"




# Get IP address of the current pod from the env var provided by Kubernetes
# pod_ip = os.environ["POD_IP"]
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
# clients = spark.run_query("drop table dwh_fact.customers_total_tevenue;")

predictions = model.predict(clients)

# Prepare a 2D array called 'predictions' of the format:
    # [
    #     [client_id_1, month_1, prediction]
    #     ,[client_id_2, month_2, prediction]
    #     ...
    # ]
# client_ids = clients['clientID'].values
# client_ids = np.array(client_ids).reshape(len(client_ids), 1)
predictions = np.array(predictions).reshape(len(predictions), 1)

# print('client_ids: ', client_ids)
# print('predictions: ', predictions)

predictions = np.concatenate((clients.values, predictions), axis = 1)
# print('predictions: ', predictions)

# Start a new Spark Session for saving data in Iceberg catalog. Use Kubernetes as a resource manager (master) to start a new Spark dirver.
# We don't use here Spark Thrift Server driver and we need to provide the same Spark configuration as for the Thrift Server.
# Most of the parameters we use here are explained at the top of the script. Regarding other parameters:
#   - bindAddress - IP address to which Spark driver will bind (it will listen on that IP). That should be IP of the pod where we run this script
#   - driver and blockManager port - might be needed (I am not sure) so driver can bind to a proper port (start listening on that port)
spark = SparkSession.builder \
    .appName("write_iceberg") \
    .master("k8s://https://kubernetes.default.svc") \
    .config("spark.kubernetes.namespace", namespace) \
    .config("spark.executor.instances", instances) \
    .config("spark.kubernetes.container.image", container_image) \
    .config("spark.driver.bindAddress", "0.0.0.0") \
    .config("spark.driver.host", driver_host) \
    .config("spark.driver.port", 7077) \
    .config("spark.blockManager.port", 7078) \
    .getOrCreate()

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