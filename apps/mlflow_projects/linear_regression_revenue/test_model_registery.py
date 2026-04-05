"""
This is a script for testing MLflow code related to registered models.
"""

import sys, pathlib

# Add "apps" folder to the sys.path so we can import from "apps/common"
sys.path.append(str(pathlib.Path(__file__).parent.parent.parent.resolve()))

from common.mlflow.my_mlflow import MyMLflow
from common.postgresql import PostgreSQL

import mlflow
import pandas as pd
import numpy as np


my_mlflow = MyMLflow()

# postgresql = PostgreSQL(
#     host="postgres.mlflow.svc"
#     ,database="mlflow"
#     ,user="mlflow"
#     ,password="mlflow"
#     ,port=5432
# )
# print(models)


# =============== Set up an alias for a registered model ===================

my_mlflow.client.set_registered_model_alias(
    name='linear_regression_revenue'
    ,alias="Production"
    ,version=1
)


# ================== Register a model ====================

# experiment = mlflow.get_experiment_by_name('linear_regression_revenue')
# models = my_mlflow.client.search_logged_models(experiment_ids=[experiment.experiment_id])

# for model in models:
#     print(model.model_uri)

# model_uri = 'models:/m-2ff2eace1ea44abea633582cef11eba9'
# registered_model = mlflow.register_model(model_uri, 'linear_regression_revenue_v2')