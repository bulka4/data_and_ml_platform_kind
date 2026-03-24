"""
Functions related to MLflow.
"""

from .my_mlflow_get import MyMLflowGet
from .my_mlflow_delete import MyMLflowDelete
from ..postgresql import PostgreSQL
from mlflow.tracking import MlflowClient

class MyMLflow():
    def __init__(
        self
        ,host="postgres.mlflow.svc"
        ,database="mlflow"
        ,user="mlflow"
        ,password="mlflow"
        ,port=5432
    ):
        self.get = MyMLflowGet()
        self.delete = MyMLflowDelete(
            host="postgres.mlflow.svc"
            ,database="mlflow"
            ,user="mlflow"
            ,password="mlflow"
            ,port=5432
        )
        
        self.client = MlflowClient()

        # Obejct for working with PostgreSQL which is used as MLflow metadata db
        self.postgresql = PostgreSQL(
            host=host
            ,database=database
            ,user=user
            ,password=password
            ,port=port
        )