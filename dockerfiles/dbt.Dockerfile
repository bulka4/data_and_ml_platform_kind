# Image for using dbt which connects to the Spark Thrift Server

FROM python:3.10-slim

# Install tools needed:
#   - dbt-spark[PyHive] - So we can use the 'thrift' method in the profiles.yml
#   - dbt-spark[session] - So we can use the 'session' method in the profiles.yml
#   - pyhive, thrift, thrift-sasl - For dbt to connect to the Spark Thrift server
#   - nano - For testing and debugging
RUN pip install --no-cache-dir \
    dbt-spark[PyHive] \
    dbt-spark[session] \
    pyhive \
    thrift \
    thrift-sasl \
    nano

WORKDIR /root/workspace