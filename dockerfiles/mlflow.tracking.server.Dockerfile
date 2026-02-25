# Image for running MLflow Tracking Server. Here we install packages needed to run the Tracking Server which uses Azure Storage Account 
# as an artifact store and MySQL as a backend store.

FROM python:3.9-slim

# Install tools needed (looks like they are not needed):
#   - build-essential, libpq-dev and gcc - Needed to compile psycopg2
#   - pkg-config - A helper tool to find metadata about installed libraries (like compiler flags and linker flags). Used by mysqlclient
# RUN apt-get update && apt-get install -y \
#     build-essential \
#     libpq-dev \
#     gcc \
#     && rm -rf /var/lib/apt/lists/*

# Install pip packages needed:
#   - mlflow[extras] - Using MLflow
#   - azure-storage-blob, azure-identity - Connecting to Azure Storage Account 
#   - psycopg2-binary - Connecting to PostgreSQL
RUN pip install mlflow[extras] azure-storage-blob azure-identity psycopg2-binary