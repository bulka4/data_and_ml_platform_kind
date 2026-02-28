"""
Create the 'default' schema in the Iceberg catalog 'iceberg_catalog'. This schema is required so we can use Spark with this config:
- spark.sql.defaultCatalog=iceberg_catalog

which uses the iceberg_catalog catalog as the default one. If we try to use Spark with this config, it throughs an error that there is no
'default' schema.

The defaultCatalog config is needed so dbt can create tables in this catalog. Looks like we can't specify in dbt which catalog to use.
"""

from pyspark.sql import SparkSession

spark = SparkSession.builder \
    .appName("init-iceberg-schema") \
    .getOrCreate()

spark.sql("CREATE SCHEMA iceberg_catalog.default")
spark.stop()