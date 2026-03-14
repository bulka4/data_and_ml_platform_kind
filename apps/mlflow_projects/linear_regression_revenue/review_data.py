"""
This is a script for reviewing MLflow data about experiments and runs.
"""

import sys, pathlib

# Add "apps" folder to the sys.path so we can import from "apps/common"
sys.path.append(str(pathlib.Path(__file__).parent.parent.parent.resolve()))

from common.my_mlflow import MyMLflow
from common.postgresql import PostgreSQL

import mlflow
import pandas as pd
import numpy as np


my_mlflow = MyMLflow()


# =========== Get experiments data ===========
# experiment ID 1 is the linear_regression one
# experiments = pd.DataFrame(
#     [
#         [e.experiment_id, e.name] 
#         for e in mlflow.search_experiments()
#     ]
#     ,columns=['experiment_id', 'name']
# )
# print('Experiments:')
# print(experiments)
# print(mlflow.search_experiments()[0])



# =========== Get runs data ===========
experiment = mlflow.get_experiment_by_name('linear_regression_revenue')

runs = mlflow.search_runs(
    experiment_ids=[experiment.experiment_id]
)
print('runs data:')
print(runs[["experiment_id", "run_id", "artifact_uri", "start_time", "tags.mlflow.runName"]])
# print(runs.columns)



# =========== Get logged models data ===============

experiment = mlflow.get_experiment_by_name('linear_regression_revenue')
# run_id = '1e23ffffbda3403eba361716332847d2'

models = my_mlflow.client.search_logged_models(
    experiment_ids=[experiment.experiment_id]
    # ,filter_string=f"source_run_id='{run_id}'"
)
print('\nmodels:')
for model in models:
    print(model)