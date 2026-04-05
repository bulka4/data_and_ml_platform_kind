"""
This is a class for interacting with Spark Thrift Server.
"""

import pandas as pd
from pyhive import hive

class SparkThrift:
    def __init__(
        self
        ,host='spark-thrift-server'
        ,port=10000
        ,auth='NONE' # No authentication. Other options include 'LDAP', 'KERBEROS', etc.
    ):
        # Connect to Spark Thrift Server
        self.conn = hive.Connection(
            host=host
            ,port=port
            ,auth=auth              
        )


    def run_query(self, query):
        """
        Run the query without returning any results
        """
        # Create a cursor
        cursor = self.conn.cursor()

        # Execute your query
        cursor.execute(query)

    
    def read_query(self, query, date_columns: list[str] = None):
        """
        The date_columns argument is a list of column names which we want to convert into the datetime type. Otherwise, they will be of the
        'object' type.
        """
        # Create a cursor
        cursor = self.conn.cursor()

        # Execute your query
        cursor.execute(query)

        # Fetch results
        rows = cursor.fetchall()

        # Get column names
        columns = [col[0] for col in cursor.description]

        # Convert to DataFrame
        df = pd.DataFrame(rows, columns=columns)

        # Convert date columns
        if date_columns != None:
            for col in date_columns:
                df[col] = pd.to_datetime(df[col])

        return df
    
    