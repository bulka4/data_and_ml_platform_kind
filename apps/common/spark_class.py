"""
This is a class for interacting with Spark Thrift Server.
"""

import pandas as pd
from pyhive import hive

class Spark:
    def __init__(
        self
        ,host='spark-thrift-server'
        ,port=10000
        ,auth='NOSAL' # No authentication. Other options include 'LDAP', 'KERBEROS', etc.
    ):
        # Connect to Spark Thrift Server
        self.conn = hive.Connection(
            host=host
            ,port=port
            ,auth=auth              
        )

    
    def read_query(self, query):
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

        return df
    
    