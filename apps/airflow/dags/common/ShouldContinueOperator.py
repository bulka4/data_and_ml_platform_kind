from airflow.models import BaseOperator
from airflow.exceptions import AirflowSkipException
from kubernetes import client, config
import time
import json


class ShouldContinueOperator(BaseOperator):
    """
    This is a custom Airflow operator for deciding whether or not to continue with next, downstream Airflow tasks. The execute function of this operator
    returns either:
        - True (continue with next tasks)
        - or False (don't continue with next tasks)

    This operator runs a Kubernetes job using the provided YAML manifest and the value returned by this operator depends on the exit code returned by the
    process running in that job.

    If this operator decides not to progress with downstream tasks (returns False), then those tasks are just skipped, nothing is marked as failed.

    Requirements for this operator to work properly:
        - The job must save termination logs in a JSON format (or don't log them at all)

    Arguments:
        - messages_to_continue - If in the termination logs (which are in a JSON format) there will be at least one key-value pair which appears in
            the dictionary given by this arugment, we will continue executing downstream Airflow tasks
    """
    def __init__(
        self
        ,task_id: str              # ID of the Airflow task
        ,manifest                  # YAML manifest of the Kubernetes job (prepared using the Jinja.load_yaml function from the common/jinja.py module)
        ,job_name: str             # Name of the Kubernetes job
        ,namespace: str            # Namespace where to run the Kubernetes job
        ,timeout: int              # How long to wait for the job to complete (in seconds) before marking the task as failed
        ,messages_to_continue: dict
        ,delete_job: bool = False  # Whether or not to delete the job after completion
        ,**kwargs
    ):
        super().__init__(task_id=task_id, **kwargs)
        
        if messages_to_continue is None:
            raise Exception('You need to provide the messages_to_continue parameter')

        self.manifest = manifest
        self.job_name = job_name
        self.namespace = namespace
        self.timeout = timeout
        self.delete_job = delete_job
        self.messages_to_continue = messages_to_continue


    def create_job(self, batch_v1):
        "Create a Kubernetes job using provided manifest."

        # Create a Kubernetes job
        resp = batch_v1.create_namespaced_job(
            namespace=self.manifest["metadata"]["namespace"]
            ,body=self.manifest
        )
        return resp
    

    def wait_for_job(self, batch_v1):
        "Wait for the Kubernetes job to finish."
        
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


    def get_job_pod_status_info(self, v1):
        """
        Get the termination logs from the status of the job's pod which succeeded. We need to use the wait_for_job function first
        before using this one, to make sure that job pods has been already finished.
        
        Requirements for this function to work properly:
            - We need to use the wait_for_job() function first to make sure that the job is completed.
            - The pod needs to save termination logs in a JSON format.

        This function returns:
            - message (dict) - A dictionary with pod's termination logs (pod which succeeded)
        """

        pods = v1.list_namespaced_pod(
            namespace=self.namespace
            ,label_selector=f"job-name={self.job_name}"
        )

        for pod in pods.items:
            container_status = pod.status.container_statuses[0] if pod.status.container_statuses else None
            
            if container_status and container_status.state.terminated:
                terminated = container_status.state.terminated
                if terminated.reason == 'Completed':
                    message = json.loads(terminated.message)

                    return message
        
        raise Exception('There are no completed pods for the job.')


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
            message = self.get_job_pod_status_info(v1)
            
            # Delete the finished job
            if self.delete_job:
                batch_v1.delete_namespaced_job(
                    name=self.job_name
                    ,namespace=self.namespace
                    ,body=client.V1DeleteOptions(
                        propagation_policy="Foreground"  # delete the job and its pods. Other options include: Background (pods removed asynchronously), Orphan (don't delete pods)
                    )
                )

            # should_continue indicates whether or not to progress with next, downstream Airflow tasks in the DAG
            should_continue = False

            # Check whether the message variable with pod's termination logs contains at least one specified key-value pair
            if self.messages_to_continue is not None:
                for key, value in self.messages_to_continue.items():
                    if key in message.keys() and message[key] == value:
                        should_continue = True

        except Exception as e:
            print("Job failed, fetching logs...")
            self.get_job_pod_logs(v1)
            raise e

        # Raise a skip exception to skip downstream tasks in the Airflow DAG if the should_continue variable indicates to do so
        if not should_continue:
            raise AirflowSkipException("Skipping downstream tasks")