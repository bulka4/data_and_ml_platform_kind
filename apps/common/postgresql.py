"""
This is a class for using PostgreSQL which serves as metadata db in MLflow. We can edit here for example 
information about experiments, artifacts and runs.
"""

import pandas as pd
from sqlalchemy import create_engine, text

class PostgreSQL:
    def __init__(
        self
        ,host="postgres.mlflow.svc"
        ,database="mlflow"
        ,user="mlflow"
        ,password="mlflow"
        ,port=5432
    ):
        self.engine = create_engine(f"postgresql+psycopg2://{user}:{password}@{host}:{port}/{database}")


    def run_query(self, query):
        """
        Execute the query without returning any results (for queries like deleting rows)
        """
        with self.engine.connect() as conn:
            conn.execute(text(query))
            conn.commit()


    def read_query(self, query):
        """
        Run the query and return a dataframe with results.
        """
        df = pd.read_sql(query, self.engine)

        return df