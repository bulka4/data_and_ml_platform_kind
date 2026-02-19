# Dockerfile for creating an image for running Spark Thrift Server

# Additional notes:
#   - Azure Storage Account will be used for storing data used for Spark calculations

FROM apache/spark:3.5.0

# Azure storage support (enables reading and saving data in a Storage Account)
# RUN curl -o /opt/spark/jars/hadoop-azure-3.3.4.jar \
#     https://repo1.maven.org/maven2/org/apache/hadoop/hadoop-azure/3.3.4/hadoop-azure-3.3.4.jar && \
#     curl -o /opt/spark/jars/azure-storage-blob-12.22.2.jar \
#     https://repo1.maven.org/maven2/com/azure/azure-storage-blob/12.22.2/azure-storage-blob-12.22.2.jar
