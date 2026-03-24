"""
This is a script for reviewing MLflow data about experiments and runs.
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
# experiment = mlflow.get_experiment_by_name('linear_regression_revenue')

# runs = mlflow.search_runs(
#     experiment_ids=[experiment.experiment_id]
# )
# print('runs data:')
# print(runs[["experiment_id", "run_id", "artifact_uri", "start_time", "tags.mlflow.runName", "tags.evaluated_model_uri"]])
# print(runs.columns)



# =========== Get logged models data ===============

# experiment = mlflow.get_experiment_by_name('linear_regression_revenue')
# # run_id = '1e23ffffbda3403eba361716332847d2'

# models = my_mlflow.client.search_logged_models(
#     experiment_ids=[experiment.experiment_id]
#     # ,filter_string=f"source_run_id='{run_id}'"
# )
# print('\nmodels:')
# for model in models:
#     print(model)



# ============ Get registered models =================

# Check registered models
# for rm in my_mlflow.client.search_registered_models():
#     print(rm.name)

# Check all the version of the model with the specified name
name = "linear_regression_revenue"
for mv in my_mlflow.client.search_model_versions(f"name='{name}'"):
    print(
        mv.version,
        mv.current_stage,
        mv.status,
        mv.run_id
    )
    # print(mv)
    # break


# registered_models = my_mlflow.postgresql.read_query("select * from registered_models where name = 'linear_regression_revenue'")
# model_versions = my_mlflow.postgresql.read_query("select * from model_versions where name = 'linear_regression_revenue'")

# print(registered_models.columns)
# print(model_versions.columns)
# print(model_versions[['source']])