"""
This is a script for deleting runs and experiments.
"""

import sys, pathlib

# Add "apps" folder to the sys.path so we can import from "apps/common"
sys.path.append(str(pathlib.Path(__file__).resolve().parent.parent.parent))

from common.mlflow.my_mlflow import MyMLflow
from common.postgresql import PostgreSQL

import mlflow
import pandas as pd
import numpy as np
import datetime


my_mlflow = MyMLflow()

# =========== Delete a run =================
experiment_name = 'linear_regression_revenue'

# date = datetime.datetime(2026, 4, 1, 4)
# runs = my_mlflow.get.get_runs_after_date(experiment_name, date)
# run_ids = runs.run_id.values.flatten()

run_ids = [
    'd64124b2994942a59b2195321048deb5'
]

for run_id in run_ids:
    artifact_paths = my_mlflow.delete.delete_run(
        run_id=run_id
        ,experiment_name=experiment_name
        ,hard_delete=True
    )
    print(artifact_paths)



# =========== Delete an experiment =================
# artifact_paths = my_mlflow.delete.delete_experiment('linear_regression_revenue', hard_delete=True)

# print(artifact_paths)

# We can restore the experiment if we didn't perform hard delete
# experiment = mlflow.get_experiment_by_name('linear_regression_revenue')
# my_mlflow.client.restore_experiment(experiment.experiment_id)




# =============== Delete a model from a registry ===================

# my_mlflow.delete.delete_registered_model(
#     model_name='linear_regression_revenue'
#     ,model_version='3'
#     ,hard_delete=True
# )