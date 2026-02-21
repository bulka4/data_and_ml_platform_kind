FROM ubuntu:22.04

# ========== Define build-time variables ==========

# Names of images we will build and load to kind which will be used when deploying resources on kind. Those are images for:
# - Airflow
# - Spark Thrift Server
# - Hive Metastore
# - MLflow
ARG CLUSTER_NAME=data-platform
ARG AIRFLOW_IMAGE_NAME=airflow:latest
ARG AIRFLOW_DAG_IMAGE_NAME=airflow-dag:latest
ARG SPARK_IMAGE_NAME=spark-thrift-server:latest
ARG MLFLOW_TRACKING_SERVER_IMAGE_NAME=mlflow-tracking-server:latest
ARG MLFLOW_PROJECT_IMAGE_NAME=mlflow-project:latest
ARG DBT_IMAGE_NAME=dbt:latest
# This prevents prompting user for input for example when using apt-get.
ENV DEBIAN_FRONTEND=noninteractive


# Tell Docker to use bash for the rest of the Dockerfile
SHELL ["/bin/bash", "-c"]

WORKDIR /root




# ============ Install Helm and kubectl =============

# Install Helm
RUN apt-get update && \
    apt-get -y install curl && \
    curl https://raw.githubusercontent.com/helm/helm/main/scripts/get-helm-3 | bash


# Install kubectl for interacting with a kind cluster
RUN apt-get install -y apt-transport-https ca-certificates gnupg && \
    curl -fsSL https://pkgs.k8s.io/core:/stable:/v1.28/deb/Release.key | gpg --dearmor -o /etc/apt/keyrings/kubernetes-apt-keyring.gpg && \

    # Add the GPG key and APT repository URL to the kubernetes.list. That url will be used to pull Kubernetes packages (like kubectl)
    <<EOF cat >> /etc/apt/sources.list.d/kubernetes.list
deb [signed-by=/etc/apt/keyrings/kubernetes-apt-keyring.gpg] https://pkgs.k8s.io/core:/stable:/v1.28/deb/ /
EOF

RUN apt-get update && \
    apt-get install -y kubectl && \
    apt-mark hold kubectl




# ============ Update kubeconfig file (.kube/config) ============

# Update the kubeconfig file (.kube/config) to specify IP of the Kubernetes cluster to use:
#   - host.docker.internal is the DNS name mapped to the IP of the host where this image will be running (created automatically by Docker)
#   - 6443 is the port on which cluster is listening. We specified that port in the kind-config file
RUN <<EOF cat > /root/modify_kubeconfig.sh
kubectl config set-cluster kind-$CLUSTER_NAME \
    --server=https://host.docker.internal:6443 \
    --insecure-skip-tls-verify=true
EOF

RUN \
    # Remove the '\r' sign from the script
    sed -i 's/\r$//' /root/modify_kubeconfig.sh && \
    # Make the script executable
    chmod +x /root/modify_kubeconfig.sh




# ========== Install other useful tools =============
# Install: nano
RUN apt-get install nano




# ============ Create and save a bash script for building images and loading them to kind =============

# Those images will be used for deploying different parts of the system as pods. Those are images for:
# - Airflow
# - Spark Thrift Server
# - MLflow

# Copy Dockerfiles and other files needed for building images
COPY dockerfiles /root/dockerfiles

# Save the script for building images and loading them to kind.
RUN <<EOF cat > /root/dockerfiles/build_and_load.sh
docker build -t $AIRFLOW_IMAGE_NAME -f dockerfiles/airflow.Dockerfile dockerfiles
docker build -t $AIRFLOW_DAG_IMAGE_NAME -f dockerfiles/airflow.dag.Dockerfile dockerfiles
docker build -t $SPARK_IMAGE_NAME -f dockerfiles/spark.thrift.server.Dockerfile dockerfiles
docker build -t $DBT_IMAGE_NAME -f dockerfiles/dbt.Dockerfile dockerfiles

kind load docker-image $AIRFLOW_IMAGE_NAME --name $CLUSTER_NAME
kind load docker-image $AIRFLOW_DAG_IMAGE_NAME --name $CLUSTER_NAME
kind load docker-image $SPARK_IMAGE_NAME --name $CLUSTER_NAME
kind load docker-image $DBT_IMAGE_NAME --name $CLUSTER_NAME
EOF

RUN \
    # Remove the '\r' sign from the script
    sed -i 's/\r$//' /root/dockerfiles/build_and_load.sh && \
    # Make the script executable
    chmod +x /root/dockerfiles/build_and_load.sh




# ============ Copy other needed folders ==============

# Helm charts for deploying all the resources
COPY helm_charts /root/helm_charts
# Script for creating Kubernetes namespaces and secrets
COPY create_k8s_secrets.sh /root/create_k8s_secrets.sh





# Run the script for building and pushing images to ACR and start a bash session
# CMD ["bash", "-c", "/root/dockerfiles/build_and_load.sh && /bin/bash"]