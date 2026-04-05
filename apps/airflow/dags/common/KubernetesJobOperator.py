from airflow.models import BaseOperator
from kubernetes import client, config
import time


class KubernetesJobOperator(BaseOperator):
    """
    This is a custom Airflow operator for running Kubernetes jobs. 

    Key features:
        - This operator finishes execution when the Kubernetes job is finished, not earlier
        - When Kubernetes job fails, this operator also fails
    """
    def __init__(
        self
        ,task_id: str               # ID of the Airflow task
        ,manifest                   # YAML manifest of the Kubernetes job (prepared using the Jinja.load_yaml function from the common/jinja.py module)
        ,job_name: str              # Name of the Kubernetes job
        ,namespace: str             # Namespace where to run the Kubernetes job
        ,timeout: int               # How long to wait for the job to complete (in seconds) before marking the task as failed
        ,delete_job: bool = False   # Whether or not to delete the job after completion
        ,**kwargs
    ):
        super().__init__(task_id=task_id, **kwargs)

        self.manifest = manifest
        self.job_name = job_name
        self.namespace = namespace
        self.timeout = timeout
        self.delete_job = delete_job
    

    def create_job(self, batch_v1):
        "Create a Kubernetes job using provided manifest."

        # Create a Kubernetes job
        resp = batch_v1.create_namespaced_job(
            namespace=self.manifest["metadata"]["namespace"]
            ,body=self.manifest
        )
        return resp
    

    def wait_for_job(self, batch_v1):
        "Wait for the Kubernetes job to finish. This function raises an exception when the job fails."
        
        start_time = time.time()

        while True:
            # Find the Kubernetes job
            job = batch_v1.read_namespaced_job(self.job_name, self.namespace)

            if job.status is not None:
                # Check whether the job succeeded
                if job.status.succeeded is not None and job.status.succeeded >= 1:
                    print("Job succeeded")
                    return

                # Check whether the job failed
                if (
                    job.spec.backoff_limit is not None 
                    and job.status.failed is not None 
                    and job.status.failed >= job.spec.backoff_limit
                ):
                    raise Exception("Job failed")

            time.sleep(10)

            if self.timeout is not None and time.time() - start_time > self.timeout:
                raise Exception("Job timeout")


    def get_job_pod_logs(self, v1):
        "Get logs from pods created by the job."

        pods = v1.list_namespaced_pod(
            namespace=self.namespace
            ,label_selector=f"job-name={self.job_name}"
        )

        for pod in pods.items:
            print(f"Logs from pod {pod.metadata.name}:")
            print(v1.read_namespaced_pod_log(
                name=pod.metadata.name
                ,namespace=self.namespace
            ))


    def execute(self, context):
        # Create use the client and config objects in this function, not in the __init__ function because they should be used
        # during task execution while the __init__ function is called during DAG parsing.

        # create configs with credentials used for authentication when making Rest API calls to Kubernetes API
        config.load_incluster_config()
        # Create Kubernetes API client to work with jobs (by making a Rest API call to Kubernetes)
        batch_v1 = client.BatchV1Api()
        # Create Kubernetes API client to work with pods (by making a Rest API call to Kubernetes)
        v1 = client.CoreV1Api()

        try:
            self.create_job(batch_v1)
            self.wait_for_job(batch_v1)
            # Delete the finished job
            if self.delete_job:
                batch_v1.delete_namespaced_job(
                    name=self.job_name
                    ,namespace=self.namespace
                    ,body=client.V1DeleteOptions(
                        propagation_policy="Foreground"  # delete the job and its pods. Other options include: Background (pods removed asynchronously), Orphan (don't delete pods)
                    )
                )

        except Exception as e:
            print("Job failed, fetching logs...")
            self.get_job_pod_logs(v1)
            raise e