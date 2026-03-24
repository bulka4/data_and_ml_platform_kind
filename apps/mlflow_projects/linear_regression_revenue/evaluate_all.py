"""
This script evaluates all the models from the current experiment (in which this script runs). Each evaluation is a separate run.
"""

import numpy as np
from sklearn.metrics import mean_squared_error, r2_score
import mlflow
import argparse

import os, sys, pathlib

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
    y_pred = model.predict(X_test)
    mse = mean_squared_error(y_test, y_pred)
    r2 = r2_score(y_test, y_pred)

    with mlflow.start_run() as run:
        mlflow.log_metric("mse", mse)
        mlflow.log_metric("r2", r2)
        mlflow.set_tag("evaluated_model_uri", model_info.model_uri)
        mlflow.set_tag("evaluated_model_source_run_id", model_info.source_run_id)
print("Evaluation metrics logged to MLflow backend")