"""
This DAG checks metrics related to ML model performance and if specific conditions are satisfied, then trains new models and saves the best one
in the MLflow registry.

It checks metrics by running the check_whether_to_train.py script.

It runs scripts for training and evaluating models from the MLflow project 'apps/mlflow_projects/linear_regression_revenue' on the host.

We run scripts as Kubernetes jobs defined by the train-models.yaml job manifest (we insert proper parameters into that manifest to use it for training
different models and evaluating them).

The MLflow project files from the host are mounted into the created pods.
"""

from airflow import DAG
from datetime import datetime
from time import time
import sys, pathlib


# Add the 'airflow/dags' root folder to the sys.path so we can import modules from airflow/dags/common
sys.path.append(str(pathlib.Path(__file__).parent.parent.resolve()))

from common.jinja import Jinja
from common.KubernetesJobOperator import KubernetesJobOperator
from common.ShouldContinueOperator import ShouldContinueOperator



# ============================ Configuration ============================

# Kubernetes namespace where to run the job
namespace = 'mlflow'
# Image to use in the job (use image from Dockerfile mlflow_spark or mlflow_project. The mlflow_project is smaller but mlflow_spark is more universal
# so we can use mlflow_spark for everything and don't build the mlflow_project at all).
image = 'mlflow-spark'
# Use a local image instead of trying to pull it from an online registry
image_pull_policy = 'IfNotPresent'

# Name of the experiment where to run the MLflow project
experiment_name = 'linear_regression_revenue'
model_name = 'LR_model'
# URI of the MLflow tracking server to use of the format: http://<mlflow-server-service>.<namespace>.svc:5000, where:
#   - mlflow-server-service - Name of the service that the MLflow tracking server uses
#   - namespace - Namespace where the MLflow tracking server runs
mlflow_tracking_uri = 'http://tracking-server.mlflow.svc:5000'
# DNS name of the Spark Thrift Server to connect to (to get data from it for training models) of the format: <spark-service>.<namespace>.svc, where:
#   - spark-service - Name of the service used by the Spark Thrift server
#   - namespace - Namespace where the Spark Thrift server runs
spark_thrift_server_dns = 'spark-thrift-server.spark.svc'
    


# ============================ Prepare YAML manifests ============================

jinja = Jinja()

# Base params for the job manifest, used to prepare params for manifests for jobs for training and evaluating models
base_params = {
    'job_name': None    # Name of the Kubernetes job
    ,'namespace': namespace
    ,'image': image
    ,'image_pull_policy': image_pull_policy
    ,'entrypoint': None
    ,'experiment_name': experiment_name
    ,'start_date': None
    ,'end_date': None
    ,'fit_intercept': None
    ,'positive': None
    ,'model_name': model_name
    ,'mlflow_tracking_uri': mlflow_tracking_uri
    ,'spark_thrift_server_dns': spark_thrift_server_dns
}

# Job manifest for checking whether or not a retraining of the model is needed
should_retrain_job_params = base_params.copy()
should_retrain_job_params['job_name'] = f'check-whether-to-retrain-{int(time())}'
should_retrain_job_params['metric_threshold'] = 9999999                # When metric is higher than the metric_threshold, then model requires a retraining

should_retrain_job_manifest = jinja.load_yaml('/opt/airflow/dags/update_model/check-whether-to-retrain.yaml', should_retrain_job_params)


# Job manifest for training one model. Use all months data for training
train_model_1_job_params = base_params.copy()
train_model_1_job_params['job_name'] = f'train-model-1-{int(time())}'   # Name of the Kubernetes job
train_model_1_job_params['entrypoint'] = 'train'                        # MLflow project entrypoint to run
train_model_1_job_params['start_date'] = '2025-01-01'                   # The 'start_date' parameter for the MLflow project entrypoint
train_model_1_job_params['end_date'] = '2025-06-01'                     # The 'end_date' parameter for the MLflow project entrypoint
train_model_1_job_params['fit_intercept'] = True                        # The 'fit_intercept' parameter for the MLflow project entrypoint
train_model_1_job_params['positive'] = True                             # The 'positive' parameter for the MLflow project entrypoint

train_model_1_job_manifest = jinja.load_yaml('/opt/airflow/dags/update_model/train-models.yaml', train_model_1_job_params)


# Job manifest for training the second model
train_model_2_job_params = base_params.copy()
train_model_2_job_params['job_name'] = f'train-model-2-{int(time())}'
train_model_2_job_params['entrypoint'] = 'train'
train_model_2_job_params['start_date'] = '2025-01-01'
train_model_2_job_params['end_date'] = '2025-06-01'
train_model_2_job_params['fit_intercept'] = False
train_model_2_job_params['positive'] = False

train_model_2_job_manifest = jinja.load_yaml('/opt/airflow/dags/update_model/train-models.yaml', train_model_2_job_params)


# Job manifest for evaluating all the models from the experiment (not only those which we create in this pipeline but also old models created earlier)
# Use for evaluation the last two months
eval_all_job_params = base_params.copy()
eval_all_job_params['job_name'] = f'evaluate-models-{int(time())}'
eval_all_job_params['entrypoint'] = 'eval_all'
eval_all_job_params['start_date'] = '2025-05-01'
eval_all_job_params['end_date'] = '2025-06-01'

eval_all_job_manifest = jinja.load_yaml('/opt/airflow/dags/update_model/evaluate-models.yaml', eval_all_job_params)


# Job manifest for moving the model with the best metrics to the 'Production' stage and previous model from the 'Production' stage move to the 'Archived' stage
promote_model_job_params = base_params.copy()
promote_model_job_params['job_name'] = f'promote-model-{int(time())}'
promote_model_job_manifest = jinja.load_yaml('/opt/airflow/dags/update_model/promote-model.yaml', promote_model_job_params)


# ============================ DAG ============================

default_args = {
    "owner": "airflow"
    ,"start_date": datetime(2026, 1, 1)
}

with DAG(
    "update_model"
    ,default_args=default_args
    ,schedule_interval=None
) as dag:
    # This task checks whether or not the model requires retraining. The workflow looks like that:
    #   - The ShouldContinueOperator operator runs a Kubernetes job specified by the 'check-whether-to-retrain.yaml' manifest which checks metrics
    #       about model's performance saved in the Iceberg catalog 
    #   - The job's pod saves a JSON in its termination logs indicating whether or not the model requires retraining.
    
    # Depending on whether or not termination logs contain the "should_retrain: True" key-value pair specified by the messages_to_continue argument
    # of this operator, we will either continue with executing downstream tasks or skip them:
    # - If termination logs contains the "should_retrain: True" key-value pair, then we continue executing downstream tasks to retrain the model.
    # - Otherwise, this operator raises AirflowSkipException which causes that all the next tasks are skipped.
    should_retrain = ShouldContinueOperator(
        task_id='check_whether_to_retrain'
        ,manifest=should_retrain_job_manifest
        ,job_name=should_retrain_job_params['job_name']
        ,namespace=namespace
        ,timeout=3600
        ,delete_job=True
        ,messages_to_continue={'should_retrain': True}
    )
    

    # Run the entrypoint for training from the MLflow project as a Kubernetes job
    train_model_1 = KubernetesJobOperator(
        task_id='train_model_1'
        ,manifest=train_model_1_job_manifest
        ,job_name=train_model_1_job_params['job_name']
        ,namespace=namespace
        ,timeout=3600
        ,delete_job=True
    )
    
    # Run the entrypoint for training from the MLflow project as a Kubernetes job
    train_model_2 = KubernetesJobOperator(
        task_id='train_model_2'
        ,manifest=train_model_2_job_manifest
        ,job_name=train_model_2_job_params['job_name']
        ,namespace=namespace
        ,timeout=3600
        ,delete_job=True
    )

    # Run the entrypoint for evaluating all models in the experiment (not only those which we just created but also old models created earlier)
    # from the MLflow project as a Kubernetes job
    evaluate_all = KubernetesJobOperator(
        task_id='evaluate_all'
        ,manifest=eval_all_job_manifest
        ,job_name=eval_all_job_params['job_name']
        ,namespace=namespace
        ,timeout=3600
        ,delete_job=True
    )

    # Move the model with the best metrics to the 'Production' stage and previous model from the 'Production' stage move to the 'Archived' stage
    promote_model = KubernetesJobOperator(
        task_id='promote_model'
        ,manifest=promote_model_job_manifest
        ,job_name=promote_model_job_params['job_name']
        ,namespace=namespace
        ,timeout=3600
        ,delete_job=True
    )

    # Train all the models in parallel, then evaluate all the models from the experiment and at the end promote the best model
    should_retrain >> [train_model_1, train_model_2] >> evaluate_all >> promote_model