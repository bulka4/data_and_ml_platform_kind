"""
This is a test script for saving data using Spark running in the client mode (Spark driver runs on the same server where we run this script).

This script is supposed to be run without using Spark Operator, it can be ran on its own.

It is the best to use it in the pod created using the "helm_charts/development_pods/mlflow" Helm chart (it prepares environment for running MLflow 
but Spark as well).
"""

import os, sys, pathlib

# Add "apps" folder to the sys.path so we can import from "apps/common"
sys.path.append(str(pathlib.Path(__file__).parent.parent.parent.parent.resolve()))

from common.spark_thrift_class import SparkThrift
from pyspark.sql import SparkSession
import numpy as np

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

data = [[1,1], [2,2]]


# Connect to the Spark Thrift Server (Kubernetes pod) for reading data from Iceberg catalog
spark_thrift = SparkThrift(
    # Spark Kubernetes pod has a DNS name of the format: <service-name>.<namespace>.svc
    host='spark-thrift-server.spark.svc'
    ,port=10000
    ,auth='NONE'
)


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

spark_df = spark.createDataFrame(data, schema=['clientID', 'predictedRevenue'])

# Create the Iceberg table if it doesn't exist yet
spark_thrift.run_query("""
CREATE TABLE IF NOT EXISTS dwh_fact.client_total_revenue_predictions (
    clientID INT
    ,predictedRevenue int
)
USING ICEBERG
""")

# Add records to the Iceberg table
spark_df.writeTo("dwh_fact.client_total_revenue_predictions").append()