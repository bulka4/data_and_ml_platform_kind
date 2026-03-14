# Image for using MLflow and Spark (in MLflow projects, Airflow DAGs):
#   - Loading and saving models
#   - Loading data for training and saving model predictions using Spark

FROM python:3.11-slim

# Install tools needed:
# - dash: For using 'sh' shell. Needed because when deploying a Job running MLflow project, we execute the command "sh -c "mlflow run ...""
# - git: Required to run a MLflow project
RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    dash \
    && rm -rf /var/lib/apt/lists/*

# Copy and install Python libraries used in the MLflow project
COPY requirements.txt /root/requirements.txt

RUN pip install -r /root/requirements.txt

WORKDIR /root