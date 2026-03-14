"""
This is a script for testing code.
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

postgresql = PostgreSQL(
    host="postgres.mlflow.svc"
    ,database="mlflow"
    ,user="mlflow"
    ,password="mlflow"
    ,port=5432
)



# =========== Load the latest model ============
# experiment_name = 'linear_regression_revenue'
# latest_model = my_mlflow.load_latest_model(experiment_name)
# print(type(latest_model))



# ========= Check experiment models ============
# experiment = mlflow.get_experiment_by_name('linear_regression_revenue')
# experiment_model_uris = my_mlflow.find_experiment_model_uris(experiment.experiment_id)
# print(experiment_model_uris)


# result = postgresql.read_query('SELECT table_name FROM information_schema.tables')
# print(result)
# postgresql.run_query('select * from logged_models')
# postgresql.run_query('delete from logged_models where ')

# result = postgresql.run_query(f"""
#     DELETE
#     FROM logged_models
#     WHERE model_id != 'm-5f4463d9c7e24c8ab4c7e9bd40c0bbd1';
# """)
# print(result)