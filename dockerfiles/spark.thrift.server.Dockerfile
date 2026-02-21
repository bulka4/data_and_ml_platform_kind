# Dockerfile for creating an image for running Spark Thrift Server

# Additional notes:
#   - Azure Storage Account will be used for storing data warehouse data used for Spark calculations

FROM apache/spark:3.5.0

# Azure storage support (enables reading and saving data in a Storage Account)
RUN wget https://repo1.maven.org/maven2/org/apache/hadoop/hadoop-azure/3.3.6/hadoop-azure-3.3.6.jar -P /opt/spark/jars/ \
 && wget https://repo1.maven.org/maven2/com/microsoft/azure/azure-storage/8.6.6/azure-storage-8.6.6.jar -P /opt/spark/jars/ \
 && wget https://repo1.maven.org/maven2/org/apache/hadoop/hadoop-azure-datalake/3.3.6/hadoop-azure-datalake-3.3.6.jar -P /opt/spark/jars/