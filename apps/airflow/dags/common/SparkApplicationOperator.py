from airflow.models import BaseOperator
from kubernetes import client, config
import time

class SparkApplicationOperator(BaseOperator):
    """
    This is a custom Airflow operator for creating a SparkApplication resource on Kubernetes (for running Spark jobs).

    Key features:
        - This operator finishes execution when the SparkApplication is finished, not earlier
        - When SparkApplication fails, this operator also fails
    """
    def __init__(
        self
        ,task_id: str               # ID of the Airflow task
        ,namespace: str             # Namespace where to create SparkApplication
        ,resource_name: str         # Name of the SparkApplication resource to create
        ,manifest                   # YAML manifest of the SparkApplication resource to create (prepared using the Jinja.load_yaml function from the common/jinja.py module)
        ,delete_spark_application: bool = False   # Whether or not to delete the SparkApplication resource after completion
        ,**kwargs
    ):
        super().__init__(task_id=task_id, **kwargs)

        self.namespace = namespace
        self.resource_name = resource_name
        self.manifest = manifest
        self.delete_spark_application = delete_spark_application


    def create_spark_application(self, api):
        """
        Create a SparkApplication resource.
        
        Arguments:
            - api - An object created using client.CustomObjectsApi() function which represents a Kubernetes API client to work with SparkApplication resources
                (by making a Rest API call to Kubernetes)
        """
        # Create SparkApplication resource by making a Rest API call to Kubernetes
        api.create_namespaced_custom_object(
            group="sparkoperator.k8s.io"
            ,version="v1beta2"
            ,namespace=self.namespace
            ,plural="sparkapplications"
            ,body=self.manifest
        )


    def wait_for_spark_application(self, api):
        """
        Wait for the SparkApplication to complete so when Airflow task is finished, deploying SparkApplication resource is also finished.
        When SparkApplication fails, Airflow task also fails.
        
        Arguments:
            - api - An object created using client.CustomObjectsApi() function which represents a Kubernetes API client to work with SparkApplication resources
                (by making a Rest API call to Kubernetes)
        """

        while True:
            resp = api.get_namespaced_custom_object(
                group="sparkoperator.k8s.io"
                ,version="v1beta2"
                ,namespace=self.namespace
                ,plural="sparkapplications"
                ,name=self.resource_name
            )

            if "status" in resp and "applicationState" in resp["status"]:
                state = resp["status"]["applicationState"]["state"]

                if state == "COMPLETED":
                    break
                if state == "FAILED":
                    raise Exception("Spark failed")

            time.sleep(10)


    def get_job_pod_logs(self, v1):
        """
        Get logs from pods created by the Spark operator.
        
        Arguments:
            - v1 - An object created using client.CoreV1Api() function which represents a Kubernetes API client to work with pods (by making a Rest API call to Kubernetes)
        """
        # Find the Spark driver pod created by the Spark operator
        driver_pod = v1.list_namespaced_pod(
            namespace=self.namespace
            ,label_selector=f"{self.resource_name}-driver"
        )[0]

        print(f"Logs from pod {driver_pod.metadata.name}:")
        print(v1.read_namespaced_pod_log(
            name=driver_pod.metadata.name
            ,namespace=self.namespace
        ))


    def execute(self, context):
        # Create use the client and config objects in this function, not in the __init__ function because they should be used
        # during task execution while the __init__ function is called during DAG parsing.

        # create configs with credentials used for authentication when making Rest API calls to Kubernetes API
        config.load_incluster_config()
        # Create Kubernetes API client to make Rest API calls to Kubernetes
        api = client.CustomObjectsApi()
        # Create Kubernetes API client to work with pods (by making a Rest API call to Kubernetes)
        v1 = client.CoreV1Api()

        try:
            self.create_spark_application(api)
            self.wait_for_spark_application(api)
            # Delete the finished SparkApplication
            if self.delete_spark_application:
                api.delete_namespaced_custom_object(
                    group="sparkoperator.k8s.io"
                    ,version="v1beta2"          # depends on the Spark Operator version
                    ,namespace=self.namespace
                    ,plural="sparkapplications"
                    ,name=self.resource_name
                    ,body=client.V1DeleteOptions()
                )
        except Exception as e:
            print("Job failed, fetching logs...")
            self.get_job_pod_logs(v1)
            raise e