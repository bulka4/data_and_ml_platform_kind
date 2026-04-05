"""
This script checks whether or not a specific ML model requires retraining based on metrics about its performance (saved in the Iceberg catalog).

It saves a JSON in termination logs of the pod running this script that can be checked after the pod is finished and used to determine whether 
or not the model requires retraining:
    - {"should_retrain": True} - Retraining needed
    - {"should_retrain": False} - No retraining needed

This script requires environment variables to be provided:
    - SPARK_THRIFT_SERVER_DNS - DNS name of the Spark Thrift Server to connect to (to get data from it about metrics).
    - METRIC_THRESHOLD - When metric is higher than this threshold, then model requires a retraining
"""

import os, sys, pathlib
import json

# Add "apps" folder to the sys.path so we can import from "apps/common"
sys.path.append(str(pathlib.Path(__file__).parent.parent.parent.parent.resolve()))

from common.spark_thrift_class import SparkThrift


def add_json_to_termination_logs(dict: dict):
    "Add a JSON to termination logs of the pod running this script."

    with open("/dev/termination-log", "w") as f:
        f.write(json.dumps(dict))


# DNS name of the Spark Thrift Server to connect to (to get data from it about metrics).
spark_host = os.getenv('SPARK_THRIFT_SERVER_DNS')
# When metric is lower than this threshold, then model requires a retraining
threshold = float(os.getenv('METRIC_THRESHOLD'))

spark = SparkThrift(
    host=spark_host,   # DNS name of the Spark Thrift Server of the format: "<service-name>.<namespace>.svc.cluster.local"
    port=10000, 
    auth='NONE' # No authentication. Other options include 'LDAP', 'KERBEROS', etc.
)

# Take the RMSE value for the latest 1 month
query = f"""
SELECT
    RMSE_1
FROM
    dwh_ml_metrics.clients_total_revenue_predictions_metrics
ORDER BY
    month desc
LIMIT
    1
"""

metric_value = spark.read_query(query).values[0][0]

if metric_value > threshold:
    # Save a JSON in termination logs indicating whether or not the model requires retraining (it can be read from pod's status after it is finished)
    add_json_to_termination_logs({"should_retrain": True})
else:
    # Save a JSON in termination logs indicating whether or not the model requires retraining (it can be read from pod's status after it is finished)
    add_json_to_termination_logs({"should_retrain": False})