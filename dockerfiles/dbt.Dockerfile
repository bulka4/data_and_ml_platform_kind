# Image for using dbt which connects to the Spark Thrift Server

FROM python:3.10-slim

RUN pip install --no-cache-dir \
    dbt-spark[PyHive] \
    pyhive \
    thrift \
    thrift-sasl

WORKDIR /root/workspace