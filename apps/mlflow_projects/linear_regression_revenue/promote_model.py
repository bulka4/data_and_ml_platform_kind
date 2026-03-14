"""
This script saves in the MLflow registry model with the best performance. 

The following assumptions must be met:
    - We have been evaluating a single model in a single MLflow run
    - Each run was logging evaluation metrics
    - Each run got assigned tag "evaluated_model_uri" indicating which model has been evaluated
"""

import numpy as np
from sklearn.metrics import mean_squared_error, r2_score
import mlflow
from mlflow.tracking import MlflowClient
import mlflow.pyfunc
import argparse

import sys, pathlib

# Add "apps" folder to the sys.path so we can import from "apps/common"
sys.path.append(str(pathlib.Path(__file__).parent.parent.parent.resolve()))

from common.my_mlflow import MyMLflow


# ================= Script configuration =================

# Name of the experiment from which we want to promote the model
experiment_name = 'linear_regression_revenue'

# Metrics based on which we want to find the best model using the my_mlflow.get_the_best_run function.
# It is a dictionary specifying names of metrics and whether we want to get a run with the highest or lowest values of those metrics.
# It is of the following format:
#       {
#           'metric_1_name': 'highest'   # Get the run with highest value of this metric
#           ,'metric_2_name': 'lowest'   # Get the run with the lowest value of this metric
#       }
metrics = {'mse': 'lowest', 'r2': 'highest'}



# ================= Register the model with the best performance =================

my_mlflow = MyMLflow()
client = MlflowClient()

# Find a model with the best metrics. he following assumptions must be met:
#    - We have been evaluating a single model in a single MLflow run
#    - Each run was logging evaluation metrics
#    - Each run got assigned tag "evaluated_model_uri" indicating which model has been evaluated
model_uri = my_mlflow.get_the_best_model_uri(experiment_name=experiment_name, metrics=metrics)

# Register the model
mlflow.register_model(model_uri, "linear_regression_revenue")

# Assign model version and stage
client.transition_model_version_stage(
    name="linear_regression_revenue",
    version=1,
    stage="Production"
)

# Test loading the model
# model = mlflow.pyfunc.load_model("models:/linear_regression_revenue/Production")
# print(model)