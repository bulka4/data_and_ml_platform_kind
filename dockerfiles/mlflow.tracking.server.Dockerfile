# Image for running MLflow Tracking Server. Here we install packages needed to run the Tracking Server which uses Azure Storage Account 
# as an artifact store and MySQL as a backend store.

FROM python:3.9-slim

# Install pip packages needed:
#   - mlflow[extras] - Using MLflow
#   - azure-storage-blob, azure-identity - Connecting to Azure Data Lake Gen2 (using "wasbs" url scheme (i.e. url wasbs://{containerName}@{STORAGE_ACCOUNT_NAME}.blob.core.windows.net))
#   - psycopg2-binary - Connecting to PostgreSQL used as a backend store
RUN pip install mlflow[extras] azure-storage-blob azure-identity psycopg2-binary