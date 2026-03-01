from airflow.providers.cncf.kubernetes.operators.kubernetes_pod import KubernetesPodOperator
from kubernetes.client import (
    V1Volume, V1VolumeMount, V1EmptyDirVolumeSource, V1ResourceRequirements, V1Container, V1PodSpec
)
# from kubernetes.client import models as k8s

from airflow import DAG
from datetime import datetime


# =============== Configuration ===============
image = "dbt:latest" # Include only lowercase letters
# URL of a git repo with code to run
repo_url = "https://github.com/bulka4/data_and_ml_platform_kind.git"
# Path to the dbt project. That project needs to have the following file structure:
#   |-- .dbt
#       |-- profiles.yml
#   |-- workspace
#       |-- macros
#       |-- models
#       |-- dbt_project.yml
dbt_project_path = "apps/dbt"
# Commit from which to take the code (leave an empty string to take the latest one)
commit = ""

# script_to_run = "/opt/airflow/dags/project_1/task_1.py"
# pvc_name = "airflow-dags-pvc" # Name of the PVC with saved DAGs code (pulled by git-sync)
# airflow_logs_url = "wasb://airflow-logs@systemfilesbulka.blob.core.windows.net" # URL of the Storage Account used for saving Airflow logs
# conn_id = "azure_blob" # ID of the Airflow connection used for accessing Azure Storage Account for saving Airflow logs



# =============== DAG ===============
default_args = {
    "owner": "airflow"
    ,"start_date": datetime(2026, 1, 1)
}

with DAG(
    "example_pod_with_git_sync"
    ,default_args=default_args
    ,schedule_interval=None
) as dag:

    task = KubernetesPodOperator(
        task_id="dbt_task"
        ,name="dbt"
        ,namespace="spark"
        ,containers=[
            V1Container(
                name="dbt"
                ,image=image
                ,image_pull_policy="IfNotPresent"   # don't pull an image from a remote registry but use a local one instead (for testing on kind)
                # ,service_account_name="airflow-sa" # K8s Service Account with a secret for pulling images
                # ,image_pull_secrets="" # Name of the secret for pulling images from a registry
                ,command=["dbt", "run"]
                ,resources=V1ResourceRequirements(
                    requests={"memory": "512Mi", "cpu": "500m"},
                    limits={"memory": "1Gi", "cpu": "1"},
                )
                ,volume_mounts=[
                    V1VolumeMount(
                        name="git-repo",
                        mount_path="/root",
                        sub_path=dbt_project_path  # replace with the git path
                    )
                ]
            )
        ]
        # ,volumes=[dags_volume]
        # ,volume_mounts=[dags_volume_mount]
        ,volumes=[
            V1Volume(
                name="git-repo",
                empty_dir=V1EmptyDirVolumeSource()
            )
        ]
        ,init_containers=[
            V1Container(
                name="git-init",
                image="alpine/git:latest",
                command=["sh", "-c"],
                args=[
                    f"""
                    git clone --branch main {repo_url} /repo
                    cd /repo
                    git checkout {commit} || true
                    """
                ],
                volume_mounts=[
                    V1VolumeMount(
                        name="git-repo",
                        mount_path="/repo"
                    )
                ]
            )
        ]
        ,pod_spec=V1PodSpec(restart_policy="Never")
        ,get_logs=True
        ,is_delete_operator_pod=False # don't delete the pod once the task is finished
        ,full_pod_spec=True # this allows us to provide the `containers` argument in the KubernetesPodOperator function
    )

