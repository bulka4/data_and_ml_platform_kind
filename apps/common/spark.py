"""
This is a collection of functions for working with Spark (but not with Thrift Server, for that there is a separate file spark_thrift_class.py).
"""

from pyspark.sql import SparkSession
import os

def create_session(
    app_name
    ,configs
):
    """
    This function prepares a SparkSession using provided configs. Arguments:
        - app_name - Name of the Spark app to create
        - configs - A dictionary with configs of the format:
            {
                config_name_1: value_1
                ,config_name_2: value_2
                ...
            }
            It can be prepared using the prepare_iceberg_configs function to get configs for working with Spark and Iceberg.
    """
    builder = SparkSession.builder \
        .appName(app_name)
    
    for k, v in configs.items():
        builder = builder.config(k, v)

    spark = builder.getOrCreate()

    return spark


def prepare_iceberg_configs():
    """
    This function prepares configs needed to work with Spark and Iceberg. It outputs a dictionary of the following format:
        {
            config_name_1: value_1
            ,config_name_2: value_2
            ...
        }
    which can be used to create a SparkSession using for example the 'create_session' function from this script.

    It requires to prepare the following environment variables first:
        - STORAGE_ACCOUNT, CONTAINER - Name of the Azure Storage Account and container used as an Iceberg catalog (data warehouse)
        - SA_ACCESS_KEY - Access key to the Storage Account used
        - CATALOG_FOLDER - Folder in the Storage Account container used as an Iceberg catalog (to store all the data)
    """
    configs = {
        # Set the default filesystem. Used when reading / writing data.
        'spark.hadoop.fs.defaultFS': f"abfss://{os.environ['CONTAINER']}@${os.environ['STORAGE_ACCOUNT']}.dfs.core.windows.net/"

        # Config for authentication to Azure Storage Account (to be able to read and save data). STORAGE_ACCOUNT is a name of the Storage Account
        # to use and SA_ACCESS_KEY is an access key to it.
        ,f"spark.hadoop.fs.azure.account.key.{os.environ['STORAGE_ACCOUNT']}.dfs.core.windows.net": f"{os.environ['SA_ACCESS_KEY']}"
        
        # Add additional iceberg extensions providing additional functionalities (e.g. merge, time travel)
        ,'spark.sql.extensions': f'org.apache.iceberg.spark.extensions.IcebergSparkSessionExtensions'
        
        # Below spark.sql.catalog.iceberg_catalog configs define Iceberg catalog (called "iceberg_catalog", this is a name we can choose here)
        
        # Define the class used to perform operations on tables from the "iceberg_catalog" catalog
        ,'spark.sql.catalog.iceberg_catalog': 'org.apache.iceberg.spark.SparkCatalog'
        # Define to store metadata of tables from the "iceberg_catalog" catalog in the filesystem (defined by the next iceberg_catalog.warehouse config)
        ,'spark.sql.catalog.iceberg_catalog.type': 'hadoop'
        # Define where to store data of tables from the "iceberg_catalog" catalog
        ,'spark.sql.catalog.iceberg_catalog.warehouse': f"abfss://{os.environ['CONTAINER']}@{os.environ['STORAGE_ACCOUNT']}.dfs.core.windows.net/{os.environ['CATALOG_FOLDER']}/"

        # Set up the iceberg_catalog as a default catalog. When we create a table without specifying a catalog, this catalog will be used.
        # It is needed for dbt since it creates tables without specifying catalog and it looks like we can't specify the catalog there.
        ,'spark.sql.defaultCatalog': 'iceberg_catalog'
    }

    return configs