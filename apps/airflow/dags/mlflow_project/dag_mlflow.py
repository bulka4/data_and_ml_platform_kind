from airflow.providers.cncf.kubernetes.operators.kubernetes_pod import KubernetesPodOperator
from kubernetes.client import (
    V1Volume, V1VolumeMount, V1EmptyDirVolumeSource, V1ResourceRequirements, V1Container, V1PodSpec
)
# from kubernetes.client import models as k8s

from airflow import DAG
from datetime import datetime


# =============== Configuration ===============




# =============== DAG ===============
default_args = {
    "owner": "airflow"
    ,"start_date": datetime(2026, 1, 1)
}

with DAG(
    "mlflow_project"
    ,default_args=default_args
    ,schedule_interval=None
) as dag:

    task = KubernetesPodOperator(
        task_id="mlflow_task"
        # ,name="dbt"
        # ,namespace="spark"
        ,pod_template_file="/opt/airflow/dags/project_1/mlflow-job.yaml"  # full pod manifest
        ,get_logs=True
        ,is_delete_operator_pod=False # don't delete the pod once the task is finished
    )