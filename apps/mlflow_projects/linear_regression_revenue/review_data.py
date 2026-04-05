"""
This is a script for reviewing MLflow data about experiments, runs, models.
"""

import sys, pathlib

# Add "apps" folder to the sys.path so we can import from "apps/common"
sys.path.append(str(pathlib.Path(__file__).parent.parent.parent.resolve()))

from common.mlflow.my_mlflow import MyMLflow
from common.postgresql import PostgreSQL

import mlflow
import pandas as pd
import numpy as np
import datetime


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

# dt = datetime.datetime(2026, 4, 1, 2, 30)
# # convert to milliseconds
# timestamp_ms = int(dt.timestamp() * 1000)

# runs = mlflow.search_runs(
#     experiment_ids=[experiment.experiment_id]
#     ,filter_string=f'start_time >= {timestamp_ms}'
# )
# print('runs data:')
# # print(runs)
# print(runs[[
#     "experiment_id", "run_id", "start_time"#, "metrics.mse", "metrics.r2"
#     #,"tags.evaluated_model_uri"#, "tags.created_model_uri"
# ]])
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

# Check all the versions of the model with the specified name
name = "linear_regression_revenue"

print('Registered model versions:')
for mv in my_mlflow.client.search_model_versions(f"name='{name}'"):
    print(
        mv.version,
        mv.current_stage,
        mv.status,
        mv.run_id,
        mv.source
    )
    
print('Registered models aliases:')
for mv in my_mlflow.client.search_registered_models(f"name='{name}'"):
    print(
        mv.aliases
    )
    print(mv)
    # break


# registered_models = my_mlflow.postgresql.read_query("select * from registered_models where name = 'linear_regression_revenue'")
# model_versions = my_mlflow.postgresql.read_query("select * from model_versions where name = 'linear_regression_revenue'")

# print(registered_models.columns)
# print(model_versions.columns)
# print(model_versions[['source']])