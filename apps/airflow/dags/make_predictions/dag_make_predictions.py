"""
This is a DAG for making predictions and saving them in the Iceberg catalog. We use a ML model from the MLflow registry and Spark to save predictions
(we don't use the Spark Thrift Server but create a new Spark driver using Spark Operator).

We run a Spark script from the host which we mount into the driver and executor pods created by the Spark Operator:
    - We define that mounting in the spark-application.yaml.
    - The mainApplicationFile variable in this script specifies path to the script to run (that's path in the pod, relative to the path where volume is mounted)

Before we run this DAG we need to:
    - Provide proper values in the 'Configuration' section at the top of this script.
    - Install Spark Operator on Kubernetes
    - Prepare the service account which will be used by the Spark Operator to create Spark drvier pod (it can be created using the 
        helm_charts/spark_operator Helm chart.)
"""

from airflow import DAG
from datetime import datetime
import time
import sys, pathlib

from airflow.operators.python import PythonOperator
from kubernetes import client, config

# Add the 'airflow/dags' folder to the sys.path so we can import modules from there
sys.path.append(str(pathlib.Path(__file__).parent.resolve()))

from common.jinja import Jinja
from common.SparkApplicationOperator import SparkApplicationOperator



# =================== Configuration ========================

# Namespace where to run Spark Operator (where to run Spark driver)
namespace = 'spark'
# Name of the created SparkApplication resource
resourceName = 'pyspark-app'
imagePullPolicy = 'IfNotPresent'
# path of the Spark script to run. This is the path to the Spark script relative to the "apps" folder from this repo (because we mount
# the 'apps' folder from the host into the Spark driver and executor pods in the spark-application.yaml).
mainApplicationFile = 'airflow/dags/make_predictions/make_predictions_spark_operator.py'
# URL of the Spark image to run
image = 'mlflow-spark'
# URI of the MLflow tracking server to use of the format: http://<mlflow-server-service>.<namespace>.svc:5000, where:
#   - mlflow-server-service - Name of the service that the MLflow tracking server uses
#   - namespace - Namespace where the MLflow tracking server runs
mlflowTrackingUri = 'http://tracking-server.mlflow.svc:5000'
# DNS name of the Spark Thrift Server to connect to (to get data from it for training models) of the format: <spark-service>.<namespace>.svc, where:
#   - spark-service - Name of the service used by the Spark Thrift server
#   - namespace - Namespace where the Spark Thrift server runs
sparkThriftServerDNS = 'spark-thrift-server.spark.svc'


# Storage Account and container for storing data warehouse data used by Spark. Those params are used to prepare Spark config files.
storageAccount = {
    # Name of the Kubernetes secret with the following keys:
    #   - storage-account - Name of the Storage Account to use
    #   - sa-access-key - Access key to the Storage Account
    'secret': 'adls-sp-secret'
    ,'container': 'dwh'
}


# Name of the folder in Azure Storage Account where is located the Iceberg catalog to use (the same one as the Spark Thrift Server uses)
icebergCatalogFolder = 'iceberg-warehouse'


with DAG(
    dag_id="make_predictions",
    start_date=datetime(2026, 1, 1),
    schedule_interval=None,
    catchup=False,
) as dag:

    jinja = Jinja()
    params = {
        'namespace': namespace
        ,'resourceName': resourceName
        ,'imagePullPolicy': imagePullPolicy
        ,'mainApplicationFile': mainApplicationFile
        ,'image': image
        ,'mlflowTrackingUri': mlflowTrackingUri
        ,'sparkThriftServerDNS': sparkThriftServerDNS
        ,'storageAccount': storageAccount
        ,'icebergCatalogFolder': icebergCatalogFolder
    }

    spark_app_manifest = jinja.load_yaml('/opt/airflow/dags/make_predictions/spark-application.yaml', params)

    task = SparkApplicationOperator(
        task_id='submit_spark'
        ,namespace=namespace
        ,resource_name=resourceName
        ,manifest=spark_app_manifest
        ,delete_spark_application=True
    )


    # Old code replaced by using the SparkApplicationOperator

    # def submit_spark_app():
    #     # create configs with credentials used for authentication when making Rest API calls to Kubernetes API
    #     config.load_incluster_config()

    #     # Create Kubernetes API client to make Rest API calls to Kubernetes
    #     api = client.CustomObjectsApi()

    #     # Create SparkApplication resource by making a Rest API call to Kubernetes
    #     api.create_namespaced_custom_object(
    #         group="sparkoperator.k8s.io",
    #         version="v1beta2",
    #         namespace=namespace,
    #         plural="sparkapplications",
    #         body=spark_app_manifest,
    #     )
        
    #     # Wait until the submitted SparkApplication resource is either completed or failed (so when Airflow task is finished, 
    #     # deploying SparkApplication resource is also finished. When SparkApplication fails, Airflow task also fails).
    #     while True:
    #         resp = api.get_namespaced_custom_object(
    #             group="sparkoperator.k8s.io",
    #             version="v1beta2",
    #             namespace=namespace,
    #             plural="sparkapplications",
    #             name=resourceName,
    #         )

    #         if "status" in resp and "applicationState" in resp["status"]:
    #             state = resp["status"]["applicationState"]["state"]

    #             if state == "COMPLETED":
    #                 break
    #             if state == "FAILED":
    #                 raise Exception("Spark failed")

    #         time.sleep(10)


    # submit = PythonOperator(
    #     task_id="submit_spark",
    #     python_callable=submit_spark_app,
    # )