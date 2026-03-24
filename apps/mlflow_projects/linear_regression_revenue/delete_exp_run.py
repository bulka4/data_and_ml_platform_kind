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


my_mlflow = MyMLflow()

# =========== Delete a run =================
# experiment_name = 'linear_regression_revenue'
# for run_id in [
#     "b96cded8d8d44956adaf79ad9aa2557c"
# ]:
#     artifact_paths = my_mlflow.delete.delete_run(
#         run_id=run_id
#         ,experiment_name=experiment_name
#         ,hard_delete=True
#     )
#     print(artifact_paths)



# =========== Delete an experiment =================
artifact_paths = my_mlflow.delete.delete_experiment('linear_regression_revenue', hard_delete=True)

# print(artifact_paths)

# We can restore the experiment if we didn't perform hard delete
# experiment = mlflow.get_experiment_by_name('linear_regression_revenue')
# my_mlflow.client.restore_experiment(experiment.experiment_id)