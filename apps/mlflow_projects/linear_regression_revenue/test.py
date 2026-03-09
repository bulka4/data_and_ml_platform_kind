import sys, pathlib

# Add mlflow_projects folder to the sys.path so we can import from mlflow_projects/common
sys.path.append(str(pathlib.Path(__file__).parent.parent.resolve()))

from common.my_mlflow import MyMLflow
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
# print(runs[["experiment_id", "run_id", "artifact_uri", "start_time"]])
# print(runs.columns)



# =========== Get logged models data ===============

experiment = mlflow.get_experiment_by_name('linear_regression_revenue')
# run_id = 'c344f071746c4df0813d64db3251c87c'

models = my_mlflow.client.search_logged_models(
    experiment_ids=[experiment.experiment_id]
    # ,filter_string=f"source_run_id='{run_id}'"
)

print('models: ', models)



# =========== Delete a run =================
# experiment_name = 'linear_regression_revenue'
# for run_id in [
#     "984853238afb494d8c4d4558e83a143b"
# ]:
#     artifact_paths = my_mlflow.delete_run(run_id, experiment_name)
    # print(artifact_paths)



# =========== Delete an experiment =================
# artifact_paths = my_mlflow.delete_experiment('linear_regression_revenue')
# print(artifact_paths)

# experiment = mlflow.get_experiment_by_name('linear_regression_revenue')
# my_mlflow.client.restore_experiment(experiment.experiment_id)



# =========== Load the latest model ============
# experiment_name = 'linear_regression_revenue'
# latest_model = my_mlflow.load_latest_model(experiment_name)
# print(type(latest_model))