# This is a script for installing Spark Operator using Helm. Spark Operator can be used to run Spark jobs.

helm repo add spark-operator https://kubeflow.github.io/spark-operator
helm repo update

# Source code of the 'spark-operator' Helm chart we install here - https://github.com/kubeflow/spark-operator/blob/release-2.1/charts/spark-operator-chart/templates/controller/deployment.yaml
# Parameters:
#   - sparkOperatorVersion is of the format: v1beta2-<operator-version>-<spark-version>, where <spark-version> must match version of Spark
#       we want to run
#   - spark.jobNamespaces - Namespaces where Operator will be looking for deployed SparkApplication resources
helm install spark-operator spark-operator/spark-operator -n spark --create-namespace \
  --set sparkOperatorVersion=v1beta2-2.1.0-3.5.0 \
  --set spark.jobNamespaces={spark} \
  --set webhook.enable=true \
  --set webhook.enableCertManager=false \
  --set webhook.generateSelfSignedCert=true

# Uninstall Spark Operator
helm uninstall spark-operator -n spark