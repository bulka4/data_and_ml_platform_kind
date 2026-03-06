# Image for using dbt which connects to the Spark Thrift Server

FROM python:3.10-slim

# Install tools needed:
#   - dbt-spark[PyHive], pyhive, thrift, thrift-sasl - So we can use the 'thrift' method in the profiles.yml for connecting to the 
#           Spark Thrift Server over Thrift protocol
RUN pip install --no-cache-dir \
    dbt-spark[PyHive] \
    pyhive==0.7.0 \
    thrift==0.22.0 \
    thrift-sasl==0.4.3

# Install tools:
#   - nano - for testing and debugging
RUN apt-get update && \
    apt-get install -y \
    nano

# Path of the following format: /{username}/{dbt_project_folder}, where:
# - dbt_project_folder - folder where we will have dbt project
# - username - user we will be using to run the dbt project
WORKDIR /root/workspace