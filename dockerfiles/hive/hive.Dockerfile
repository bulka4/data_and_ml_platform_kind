# Base image with Java 11
FROM eclipse-temurin:11-jdk-jammy

# Use Hadoop version which has already Azure jars for connecting to Storage Account
ARG HADOOP_VERSION=3.3.6
ARG HIVE_VERSION=3.1.3

ENV HADOOP_HOME=/opt/hadoop
ENV HIVE_HOME=/opt/hive
ENV PATH=$PATH:$HADOOP_HOME/bin:$HIVE_HOME/bin
# DNS name of the PostgreSQL server used as metadata db for Hive Metastore (used in the entrypoint.sh)
ENV POSTGRES_DNS=hive-postgres

# Include nano for debugging
RUN apt-get update && \
    apt-get install -y curl wget nano procps netcat postgresql-client && \
    rm -rf /var/lib/apt/lists/*

# Install Hadoop
RUN wget https://downloads.apache.org/hadoop/common/hadoop-${HADOOP_VERSION}/hadoop-${HADOOP_VERSION}.tar.gz && \
    tar -xzf hadoop-${HADOOP_VERSION}.tar.gz && \
    mv hadoop-${HADOOP_VERSION} ${HADOOP_HOME} && \
    rm hadoop-${HADOOP_VERSION}.tar.gz

# Install Hive
RUN wget https://archive.apache.org/dist/hive/hive-${HIVE_VERSION}/apache-hive-${HIVE_VERSION}-bin.tar.gz && \
    tar -xzf apache-hive-${HIVE_VERSION}-bin.tar.gz && \
    mv apache-hive-${HIVE_VERSION}-bin ${HIVE_HOME} && \
    rm apache-hive-${HIVE_VERSION}-bin.tar.gz

# Download PostgreSQL JDBC driver. Add it to the ${HIVE_HOME}/lib/ folder since that folder is included in the classpath used by Hive.
# That will allow Hive to use this driver.
RUN wget https://jdbc.postgresql.org/download/postgresql-42.7.3.jar -P ${HIVE_HOME}/lib/

COPY entrypoint.sh /entrypoint.sh

RUN chmod +x /entrypoint.sh

# Add the hadoop/tools/lib folder to the Hadoop classpath. This folder contains Azure jars needed for connecting to the Azure Storage
# Account and that classpath is used by Hive. That will allow Hive to connect to Storage Account.
ENV HADOOP_CLASSPATH=/opt/hadoop/share/hadoop/tools/lib/*:$HADOOP_CLASSPATH

EXPOSE 9083

ENTRYPOINT ["/entrypoint.sh"]