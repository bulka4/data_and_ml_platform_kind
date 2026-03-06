from airflow.providers.cncf.kubernetes.operators.kubernetes_pod import KubernetesPodOperator

from airflow import DAG
from datetime import datetime
import sys, pathlib

# Add parent folder to the sys.path so we can import modules from there
sys.path.append(str(pathlib.Path(__file__).parent.resolve()))

from common.jinja import Jinja



# =============== Configuration ===============
image = "dbt:latest" # Include only lowercase letters
# URL of a git repo with code to run
repo_url = "https://github.com/bulka4/data_and_ml_platform_kind.git"
# Path to the folder with dbt project in the repo. That project folder needs to have the following file structure:
#   |-- .dbt
#       |-- profiles.yml
#   |-- workspace
#       |-- macros
#       |-- models
#       |-- dbt_project.yml
dbt_project_path = "apps/dbt"
dbt_command = 'dbt run'
# Branch and commit from which to take the code (leave commit = "" to take the latest commit)
branch = 'main'
commit = ""


# Render YAML and prepare a V1Pod Kubernetes model object needed for the full_pod_spec argument for the KubernetesPodOperator function
jinja = Jinja()
params={
    'image': image
    ,'git': {
        'branch': branch
        ,'url': repo_url
        ,'commit': commit
        ,'dbtProjectPath': dbt_project_path
    }
    ,'dbtCommand': dbt_command
}
pod_spec = jinja.prepare_pod_spec(params, "/opt/airflow/dags/dbt/dbt.yaml")


# =============== DAG ===============
default_args = {
    "owner": "airflow"
    ,"start_date": datetime(2026, 1, 1)
}

with DAG(
    "dbt"
    ,default_args=default_args
    ,schedule_interval=None
) as dag:

    task = KubernetesPodOperator(
        task_id="dbt_task"
        ,full_pod_spec=pod_spec
        ,get_logs=True
        ,is_delete_operator_pod=False # don't delete the pod once the task is finished
    )