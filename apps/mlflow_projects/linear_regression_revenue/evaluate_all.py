"""
This script evaluates all the models from the current experiment (in which this script runs). Each evaluation is a separate run.

It saves tags:
    - evaluated_model_uri - URI of the evaluated model
    - evaluated_model_source_run_id - ID of the run where the evaluated model has been created

and metrics:
    - mse
    - r2
"""

import numpy as np
from sklearn.metrics import mean_squared_error, r2_score
import mlflow
import argparse

import os, sys, pathlib

# Add "apps" folder to the sys.path so we can import from "apps/common"
sys.path.append(str(pathlib.Path(__file__).parent.parent.parent.resolve()))

from common.mlflow.my_mlflow import MyMLflow
from common.spark_thrift_class import SparkThrift


my_mlflow = MyMLflow()


# -----------------------------
# Parse arguments
# -----------------------------
parser = argparse.ArgumentParser()
parser.add_argument(
    "--start_date"
    ,type=str
    ,help="We select data for evaluation for the timeframe between the start_date and end_date perameters."
)
parser.add_argument(
    "--end_date"
    ,type=str
    ,help="We select data for evaluation for the timeframe between the start_date and end_date perameters."
)
args = parser.parse_args()


# -----------------------------
# Get environment variables values
# -----------------------------
# DNS name of the Spark Thrift Server to connect to (to get data from it for training models).
spark_host = os.getenv('SPARK_THRIFT_SERVER_DNS')


# -----------------------------
# Load test data
# -----------------------------
spark = SparkThrift(
    host=spark_host,   # DNS name of the Spark Thrift Server of the format: "<service-name>.<namespace>.svc.cluster.local"
    port=10000, 
    auth='NONE' # No authentication. Other options include 'LDAP', 'KERBEROS', etc.
)

# Take data for evaluation from a specific timeframe
query = f"""
SELECT
    next.clientID
    ,previous.revenue as revenueLastMonth
    ,next.revenue
FROM
    dwh_fact.clients_total_revenue as previous

    join dwh_fact.clients_total_revenue as next
        on next.clientID = previous.clientID
        and next.month = add_months(previous.month, 1)
WHERE
    next.month >= '{args.start_date}'
    and next.month <= '{args.end_date}'
"""

df = spark.read_query(query)
x = df[['clientID', 'revenueLastMonth']]
y = df['revenue']


# ============== Load all the models from the experiment =================
# Get the current run ID
run_id = os.environ["MLFLOW_RUN_ID"]

# Get info about the current run
run = mlflow.get_run(run_id)

# Get experiment ID and name of the current run
experiment_id = run.info.experiment_id

# Get info about models for the specified experiment
models_info = my_mlflow.client.search_logged_models(
    experiment_ids=[experiment_id]
)


# For each model start a new run, evaluate the model, save metrics and evaluated model URI
for model_info in models_info:
    model = mlflow.sklearn.load_model(model_info.model_uri)

    # -----------------------------
    # Evaluate the model
    # -----------------------------
    y_pred = model.predict(x)
    mse = mean_squared_error(y, y_pred)
    r2 = r2_score(y, y_pred)

    with mlflow.start_run() as run:
        mlflow.log_metric("mse", mse)
        mlflow.log_metric("r2", r2)
        mlflow.set_tag("evaluated_model_uri", model_info.model_uri)
        mlflow.set_tag("evaluated_model_source_run_id", model_info.source_run_id)
print("Evaluation metrics logged to MLflow backend")