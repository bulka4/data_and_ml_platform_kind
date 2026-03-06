from airflow.providers.cncf.kubernetes.operators.kubernetes_pod import KubernetesPodOperator
from kubernetes.client import V1Volume, V1VolumeMount, V1PersistentVolumeClaimVolumeSource, V1EnvVar, V1EnvVarSource, V1SecretKeySelector

from airflow import DAG
from datetime import datetime


# =============== Configuration ===============
image = "airflow-dag:latest" # Include only lowercase letters
script_to_run = "/opt/airflow/dags/project_1/task_1.py"
pvc_name = "airflow-dags-pvc" # Name of the PVC with saved DAGs code (pulled by git-sync)



# =============== DAG ===============
default_args = {
    "owner": "airflow"
    ,"start_date": datetime(2026, 1, 1)
}

with DAG(
    "python_script"
    ,default_args=default_args
    ,schedule_interval=None
) as dag:

    # Mount the PVC used by git-sync
    dags_volume = V1Volume(
        name='dags-volume'
        ,persistent_volume_claim=V1PersistentVolumeClaimVolumeSource(
            claim_name=pvc_name
        )
    )

    dags_volume_mount = V1VolumeMount(
        name='dags-volume'
        ,mount_path='/opt/airflow/dags'
        #,sub_path='dags'
        ,read_only=True
    )

    task = KubernetesPodOperator(
        task_id="run_task"
        ,name="run-task"
        ,namespace="airflow"
        ,service_account_name="airflow-sa" # K8s Service Account with a secret for pulling images
        ,image=image
        ,image_pull_policy="IfNotPresent"   # don't pull an image from a remote registry but use a local one instead (for testing on kind)
        ,volumes=[dags_volume]
        ,volume_mounts=[dags_volume_mount]
        ,cmds=["python", script_to_run]
        ,get_logs=True
        ,is_delete_operator_pod=False # don't delete the pod once the task is finished
    )