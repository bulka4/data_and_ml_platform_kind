# Dockerfile for creating an image for running Spark Thrift Server

# Additional notes:
#   - Azure Storage Account will be used for storing data warehouse data used for Spark calculations
#           We install here jars needed to work with Storage Account.

FROM apache/spark:3.5.0

# Add jars for connecting to Azure Storage Account (enables reading and saving data). Save them in the /opt/spark/jars/ folder because that folder
# is included in the Spark's classpath so that will allow Spark to use them.
# Version of Hadoop jars we download here must match the version of Hadoop we use, that is 3.3.4
RUN wget https://repo1.maven.org/maven2/org/apache/hadoop/hadoop-azure/3.3.4/hadoop-azure-3.3.4.jar -P /opt/spark/jars/ \
 && wget https://repo1.maven.org/maven2/com/microsoft/azure/azure-storage/8.6.6/azure-storage-8.6.6.jar -P /opt/spark/jars/ \
 && wget https://repo1.maven.org/maven2/org/apache/hadoop/hadoop-azure-datalake/3.3.4/hadoop-azure-datalake-3.3.4.jar -P /opt/spark/jars/