from kubernetes import client, config

config.load_incluster_config()
v1 = client.CoreV1Api()

namespace = 'spark'
resource_name = 'pyspark-app'

driver_pod = v1.list_namespaced_pod(
    namespace=namespace
    ,label_selector=f"{resource_name}-driver"
).items

print(driver_pod)