# This is an image for working with MLflow, PyHive and Spark. It can be used for example to:
#   - Load data from an Iceberg catalog using PyHive,
#   - Load a model from a MLflow registry and make predictions with it
#   - Save predictions in an Iceberg table using Spark.
#   - Run Spark Thrift Server

# It is also used for code development, i.e. we can attach VS Code to the pod running this image.

# Alternatively, instead of using this image, we could use another image where we use PyIceberg to load and save data in Iceberg. That image
# would be much smaller than this one with Spark and doesn't require mounting Spark configuration files.

# Additional notes:
#   - Azure Storage Account will be used for storing data warehouse data used for Spark calculations
#           We install here jars needed to work with Storage Account.

# FROM apache/spark:3.5.0
FROM spark:3.5.0-scala2.12-java17-python3-r-ubuntu

USER root

ENV SPARK_HOME=/opt/spark
# Use bash as the default shell
ENV SHELL=/bin/bash

# Add jars:
#   - hadoop-azure, azure-storage, hadoop-azure-datalake - For connecting to Azure Storage Account (enables reading and saving data). 
#   - iceberg-spark-runtime - For using Iceberg (so Spark can create Iceberg tables). We download file iceberg-spark-runtime-x_y-z.jar 
#       and versions x, y and z must match:
#           - x: Spark version 3.5
#           - y: Scala version 2.12
#           - z: Iceberg version 1.9.2 (must be compatible with the Spark version)

# Save them in the $SPARK_HOME/jars/ folder because that folder is included in the Spark's classpath so that will allow Spark to use them.
# Version of Hadoop jars we download here must match the version of Hadoop we use, that is 3.3.4
RUN wget https://repo1.maven.org/maven2/org/apache/hadoop/hadoop-azure/3.3.4/hadoop-azure-3.3.4.jar -P $SPARK_HOME/jars/ \
    && wget https://repo1.maven.org/maven2/com/microsoft/azure/azure-storage/8.6.6/azure-storage-8.6.6.jar -P $SPARK_HOME/jars/ \
    && wget https://repo1.maven.org/maven2/org/apache/hadoop/hadoop-azure-datalake/3.3.4/hadoop-azure-datalake-3.3.4.jar -P $SPARK_HOME/jars/ \
    && wget https://repo1.maven.org/maven2/org/apache/iceberg/iceberg-spark-runtime-3.5_2.12/1.9.2/iceberg-spark-runtime-3.5_2.12-1.9.2.jar -P $SPARK_HOME/jars/

# Install tools needed:
#   - gettext - To use envsubst to interpolate template spark-defaults.conf config file (i.e. insert values of env vars) 
#           It is used in the init container in Spark's pod.
#   - git: Required to run a MLflow project
#   - dash: For using 'sh' shell. Needed because when deploying a Job running MLflow project, we execute the command "sh -c "mlflow run ...""
#   - bash, bash-completion - For using bash shell with folder name autocompletion (when pressing tab). Bash shell will be used when connecting to
#           the container / pod running this image for debugging / code development (for example when attaching VS Code)
#   - nano - For editing text files from a terminal
RUN apt-get update && apt-get install -y \
    gettext \
    git \
    dash \
    bash bash-completion \
    nano \
    && rm -rf /var/lib/apt/lists/*

# Install Python 3.11:
#   - software-properties-common - Installs add-apt-repository, allow to add external repositories (PPAs)
#   - add-apt-repository ppa:deadsnakes/ppa - Add new repo which is a package source (we can install from it newer Python versions)
#   - python3.11-dev - Development headers needed to compile Python packages with C extensions. Required for some libraries like NumPy
#   - python3.11-venv - venv package for creating virtual environments
#   - python3.11-distutils - Utilities used by Python packaging, used during installing libraries with pip
#   - python3-pip - Install pip for installing libraries
#   - curl - For downloading files from URLs
#   - rm -rf /var/lib/apt/lists/* - Remove apt metadata
RUN apt-get update && \
    apt-get install -y software-properties-common && \
    add-apt-repository ppa:deadsnakes/ppa && \
    apt-get update && \
    apt-get install -y \
        python3.11 \
        python3.11-dev \
        python3.11-venv \
        python3.11-distutils \
        python3-pip \
        curl && \
    rm -rf /var/lib/apt/lists/*

# Make Python 3.11 default (when users will use /usr/bin/python3 path, it will run the /usr/bin/python3.11 executable)
RUN update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.11 1

# WE will install Python libraries in a virtual environment to avoid conflicts with system packages. When we have a package installed on Ubuntu
# uisng different tool than pip (but for example using apt-get) and then we try to install a different of that package version using pip, pip will try 
# to uninstall already existing version and it will not be able to do that because it was not installed with pip, and it will fail.
RUN python3.11 -m venv /opt/venv

# Add this path to PATH so when using commands like "python3" or "pip", we use those executable files from the "/opt/venv/bin" folder (so we install
# packages with pip in the venv and use them when running "python3" command).
ENV PATH="/opt/venv/bin:$PATH"

# Install and update pip
RUN python3 -m pip install --upgrade pip setuptools wheel

# Copy and install libraries from requirements.txt
COPY requirements.txt $SPARK_HOME/work-dir/requirements.txt
RUN pip install --no-cache-dir -r $SPARK_HOME/work-dir/requirements.txt

# Copy the init_iceberg_schema.py script which prepares required 'default' schema in the Iceberg catalog. More info in comments in that script.
COPY init_iceberg_schema.py $SPARK_HOME/work-dir/

# User spark has uid=gid=185
USER spark

WORKDIR $SPARK_HOME/work-dir/