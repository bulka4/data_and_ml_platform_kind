"""
This script evaluates the model from the latest run from the current experiment (in which this script runs).
"""

import numpy as np
from sklearn.metrics import mean_squared_error, r2_score
import mlflow
import argparse

import sys, pathlib

# Add mlflow_projects folder to the sys.path so we can import from mlflow_projects/common
sys.path.append(str(pathlib.Path(__file__).parent.parent.resolve()))

from common.my_mlflow import MyMLflow


my_mlflow = MyMLflow()


# -----------------------------
# Load test data (example)
# -----------------------------
np.random.seed(123)
# Prepare X_test an y_text of shape (20, 1)
X_test = np.random.rand(20, 1) * 10
y_test = 3 * X_test.squeeze() + 5 + np.random.randn(20) * 2

# print(f"MSE: {mse:.2f}, R^2: {r2:.2f}")


# -----------------------------
# Log metrics to MLflow backend store
# -----------------------------

# set up the experiment
# mlflow.set_experiment("linear_regression")

# Start a run and assign metrics to it
with mlflow.start_run() as run:
    # Get current experiment name
    exp_id = mlflow.active_run().info.experiment_id
    experiment_name = mlflow.get_experiment(exp_id).name


    # -----------------------------
    # Load the latest model for given experiment from MLflow artifact store
    # -----------------------------
    model = my_mlflow.load_latest_model(experiment_name=experiment_name)


    # -----------------------------
    # Evaluate the model
    # -----------------------------
    y_pred = model.predict(X_test)
    mse = mean_squared_error(y_test, y_pred)
    r2 = r2_score(y_test, y_pred)


    mlflow.log_metric("mse", mse)
    mlflow.log_metric("r2", r2)
print("Evaluation metrics logged to MLflow backend")
