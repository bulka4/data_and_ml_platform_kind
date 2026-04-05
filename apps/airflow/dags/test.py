from kubernetes import client, config

config.load_incluster_config()
v1 = client.CoreV1Api()

namespace = 'mlflow'
job_name = 'check-whether-to-retrain-1775016866'

pods = v1.list_namespaced_pod(
    namespace=namespace
    ,label_selector=f"job-name={job_name}"
)

for pod in pods.items:
    print(pod.status)