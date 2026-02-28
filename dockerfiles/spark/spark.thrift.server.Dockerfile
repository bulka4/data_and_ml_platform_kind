# Dockerfile for creating an image for running Spark Thrift Server

# Additional notes:
#   - Azure Storage Account will be used for storing data warehouse data used for Spark calculations
#           We install here jars needed to work with Storage Account.

FROM apache/spark:3.5.0

USER root

ENV SPARK_HOME=$SPARK_HOME

# Add jars:
#   - hadoop-azure, azure-storage, hadoop-azure-datalake - For connecting to Azure Storage Account (enables reading and saving data). 
#   - iceberg-spark-runtime - For using Iceberg (so Spark can create Iceberg tables)

# Save them in the $SPARK_HOME/jars/ folder because that folder is included in the Spark's classpath so that will allow Spark to use them.
# Version of Hadoop jars we download here must match the version of Hadoop we use, that is 3.3.4
RUN wget https://repo1.maven.org/maven2/org/apache/hadoop/hadoop-azure/3.3.4/hadoop-azure-3.3.4.jar -P $SPARK_HOME/jars/ \
    && wget https://repo1.maven.org/maven2/com/microsoft/azure/azure-storage/8.6.6/azure-storage-8.6.6.jar -P $SPARK_HOME/jars/ \
    && wget https://repo1.maven.org/maven2/org/apache/hadoop/hadoop-azure-datalake/3.3.4/hadoop-azure-datalake-3.3.4.jar -P $SPARK_HOME/jars/ \
    && wget https://repo1.maven.org/maven2/org/apache/iceberg/iceberg-spark-runtime-3.5_2.12/1.9.2/iceberg-spark-runtime-3.5_2.12-1.9.2.jar -P $SPARK_HOME/jars/

# Install tools needed to run the init_iceberg_schema.py script
RUN pip install --no-cache-dir pyspark==3.5.0

USER spark

# Copy the init_iceberg_schema.py script which prepares required 'default' schema in the Iceberg catalog. More info in comments in that script.
COPY init_iceberg_schema.py $SPARK_HOME/work-dir/