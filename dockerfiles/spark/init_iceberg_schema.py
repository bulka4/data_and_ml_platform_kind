"""
Create the 'default' schema in the Iceberg catalog 'iceberg_catalog'. 

This schema is required so we can use Spark with the spark.sql.defaultCatalog=iceberg_catalog config which uses the iceberg_catalog catalog as a default one. 

If we try to use Spark (run a SQL query) with the iceberg_catalog set as a default catalog and the 'default' schema doesn't exist, it will through an error 
that there is no 'default' schema.

In this script we can create the 'default' schema (run a SQL query) because we create a Spark session without the iceberg_catalog set as a default catalog.

The defaultCatalog config is needed so dbt can create tables in this catalog. Looks like we can't specify in dbt which catalog to use.

This script will run in the same container as Spark Thrift Server, so it will use Spark configuration prepared there.
"""

from pyspark.sql import SparkSession

# Run Spark in a local mode
spark = SparkSession.builder \
    .appName("init-iceberg-schema") \
    .getOrCreate()

spark.sql("CREATE SCHEMA IF NOT EXISTS iceberg_catalog.default")
spark.stop()