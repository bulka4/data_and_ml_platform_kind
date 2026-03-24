"""
This script evaluates the model from the latest run from the current experiment (in which this script runs).
"""

import numpy as np
from sklearn.metrics import mean_squared_error, r2_score
import mlflow
import argparse

import sys, pathlib

# Add "apps" folder to the sys.path so we can import from "apps/common"
sys.path.append(str(pathlib.Path(__file__).parent.parent.parent.resolve()))

from common.mlflow.my_mlflow import MyMLflow


my_mlflow = MyMLflow()


# -----------------------------
# Load test data (example)
# -----------------------------
np.random.seed(123)
# Prepare X_test (20, 2) and y_text of shape (20, 1)
X_test = np.random.rand(20, 2) * 10
y_test = np.random.randn(20) * 2


# -----------------------------
# Log metrics to MLflow backend store
# -----------------------------

# Start a run and assign metrics to it
with mlflow.start_run() as run:
    # Get current experiment name
    exp_id = mlflow.active_run().info.experiment_id
    experiment_name = mlflow.get_experiment(exp_id).name


    # -----------------------------
    # Load the latest model for given experiment from MLflow artifact store
    # -----------------------------
    latest_model = my_mlflow.get.find_latest_model(experiment_name=experiment_name)
    model = mlflow.sklearn.load_model(latest_model.model_uri)


    # -----------------------------
    # Evaluate the model
    # -----------------------------
    y_pred = model.predict(X_test)
    mse = mean_squared_error(y_test, y_pred)
    r2 = r2_score(y_test, y_pred)


    mlflow.log_metric("mse", mse)
    mlflow.log_metric("r2", r2)
    mlflow.set_tag("evaluated_model_uri", latest_model.model_uri)
    mlflow.set_tag("evaluated_model_source_run_id", latest_model.source_run_id)
print("Evaluation metrics logged to MLflow backend")
