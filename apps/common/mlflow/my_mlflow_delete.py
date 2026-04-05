"""
Functions related to deleting data from the MLflow metadata database.
"""

import mlflow
from mlflow.tracking import MlflowClient
import numpy as np
from ..postgresql import PostgreSQL
from .my_mlflow_get import MyMLflowGet

class MyMLflowDelete():
    def __init__(
        self
        ,host="postgres.mlflow.svc"
        ,database="mlflow"
        ,user="mlflow"
        ,password="mlflow"
        ,port=5432
    ):
        self.client = MlflowClient()
        self.get = MyMLflowGet()

        # Obejct for working with PostgreSQL which is used as MLflow metadata db
        self.postgresql = PostgreSQL(
            host=host
            ,database=database
            ,user=user
            ,password=password
            ,port=port
        )


    def delete_run(
        self
        ,run_id: str                # ID of the run to delete
        ,experiment_name: str       # Name of the experiment to which that run belongs
        ,hard_delete: bool = False  # Whether or not to perform a hard delete
    ) -> list:
        """
        Delete a run and registered models from this run. We can perform either a soft or hard delete:
            - Soft delete: The run will disappear from the UI and results of the mlflow.search_runs() function but we can still see it by using 
                search_runs(view_type=2) and restore it using the self.client.restore_run(run_id) function.
            - Hard delete: Delete all the related metadata from the metadata db. That is metadata from tables: metrics, params, tags, latest_metrics, runs,
                logged_models, model_versions, registered_models

        We need to perform a hard delete so:
            - Logged models don't appear in results of the search_logged_models function
            - (probably) to register new model with the same name and version

        This function doesn't delete models and other artifacts from this experiment saved in the artifact store but returns paths where they are saved, so we can 
        delete them manually if we want.
        """
        # ====================== Get data ======================
        experiment = mlflow.get_experiment_by_name(experiment_name)

        if experiment is None:
            raise ValueError(f"Experiment '{experiment_name}' not found")
        
        # Get data about logged models for the given experiment and run ID
        models = self.client.search_logged_models(
            experiment_ids=[experiment.experiment_id]
            ,filter_string=f"source_run_id='{run_id}'"
        )
        # Get data about the run with specified ID
        run = mlflow.get_run(run_id)
        # Get names of registered models from the run with specified ID
        registered_model_names = self.get.get_registered_model_names(run_id=run_id)



        # ====================== Soft delete ======================
        # Perform soft delete of the experiment, its runs and registered models. After that, they will not be shown in the results of the 
        # get_experiment_by_name() and search_runs() functions but there will be still data about it in the metadata db.

        # Soft delete of the run
        self.client.delete_run(run_id)
        # Soft delete of the registered models from the experiment
        for model_name in registered_model_names:
            self.client.delete_registered_model(name=model_name)



        # ====================== Hard delete ======================
        if hard_delete:
            # Delete metadata related to the run from the PostgreSQL metadata db
            self.delete_runs_metadata([run_id])

            if len(models) > 0:
                # Delete info about logged models (so they don't appear in results of the search_logged_models function)
                self.delete_logged_models_metadata([m.model_id for m in models])

                # Delete info about model versions from the registry
                self.delete_registry_models_metadata([m.model_uri for m in models])

        # Return paths where models and artifacts are saved, so we can delete them manually if we want.
        return [model.artifact_location for model in models] + [run.info.artifact_uri]


    def delete_experiment(
        self
        ,experiment_name: str
        ,hard_delete: bool = False
    ):
        """
        Delete an experiment, its runs and registered models. We can perform either a soft or hard delete:
            - Soft delete: Experiment and its runs will disappear from the UI and results of the mlflow.search_experiments() and mlflow.search_runs() functions
                but we can still see them by using the "view_type=2" argument for the search_experiments() and search_runs() functions and restore them using the
                self.client.restore_experiment(experiment_id) and self.client.restore_run(run_id) functions.
            - Hard delete: Delete all the related metadata from the metadata db. That is metadata from tables: metrics, params, tags, latest_metrics, runs,
                experiments, logged_models, model_versions, registered_models

        We need to perform a hard delete so:
            - Logged models don't appear in results of the search_logged_models function
            - We can create a new experiment with the same name as the deleted one
            - (probably) to register new model with the same name and version

        This function doesn't delete models and other artifacts from this experiment saved in the artifact store but returns paths where they are saved, so we can 
        delete them manually if we want.
        """
        # ====================== Get data ======================
        experiment = mlflow.get_experiment_by_name(experiment_name)

        if experiment is None:
            raise ValueError(f"Experiment '{experiment_name}' not found")

        # Get logged models and runs data for the given experiment
        models = self.client.search_logged_models(experiment_ids=[experiment.experiment_id])
        runs = mlflow.search_runs(experiment_ids=[experiment.experiment_id])
        # Get names of registered models from the experiment
        registered_model_names = self.get.get_registered_model_names(experiment_name=experiment_name)
        


        # ====================== Soft delete ======================
        # Perform soft delete of the experiment, its runs and registered models. After that, they will not be shown in the results of the 
        # get_experiment_by_name() and search_runs() functions but there will be still data about it in the metadata db.
        
        # Soft delete of the experiment
        mlflow.delete_experiment(experiment.experiment_id)
        # Soft delete of the experiment runs
        for run_id in runs['run_id'].values:
            self.client.delete_run(run_id=run_id)
        # Soft delete of the registered models from the experiment
        for model_name in registered_model_names:
            self.client.delete_registered_model(name=model_name)



        # ====================== Hard delete ======================
        if hard_delete:
            if len(runs['run_id'].values) > 0:
                # Delete metadata related to the run from the PostgreSQL metadata db
                self.delete_runs_metadata([run_id for run_id in runs['run_id'].values])

            if len(models) > 0:
                # Delete info about logged models (so they don't appear in results of the search_logged_models function)
                self.delete_logged_models_metadata([m.model_id for m in models])

                # Delete info about model versions from the registry
                self.delete_registry_models_metadata([m.model_uri for m in models])

            # Delete info about the experiment itself (so we can create a new experiment with the same name as the deleted one)
            self.postgresql.run_query(f"DELETE FROM experiments WHERE experiment_id={experiment.experiment_id};")

        # Return paths where models and artifacts are saved, so we can delete them manually if we want
        return np.concatenate(([model.artifact_location for model in models], runs['artifact_uri'].values))
    

    def delete_registered_model(
        self
        ,model_name: str            # Name of the model to delete
        ,model_version: str         # Version of the model to delete
        ,hard_delete: bool = False  # Whether or not to perform a hard delete (delete info about the registered model from the metadata db)
    ):
        # Soft delete
        self.client.delete_model_version(
            name=model_name,
            version=model_version
        )

        # Hard delete - delete info from the metadata db
        if hard_delete:
            self.delete_registry_models_metadata(model_names_versions=[f'{model_name}:{model_version}'])


    def delete_runs_metadata(
        self
        ,run_ids: list[str]
    ):
        """
        This function deletes from the metadata db all the info related to runs with specified IDs.
        """
        run_ids_string = ', '.join([f"'{run_id}'" for run_id in run_ids])

        self.postgresql.run_query(f"""
            DELETE FROM metrics         WHERE run_uuid in ({run_ids_string});
            DELETE FROM params          WHERE run_uuid in ({run_ids_string});
            DELETE FROM tags            WHERE run_uuid in ({run_ids_string});
            DELETE FROM latest_metrics  WHERE run_uuid in ({run_ids_string});
            DELETE FROM runs            WHERE run_uuid in ({run_ids_string});
        """)


    def delete_logged_models_metadata(
        self
        ,model_ids: list[str]
    ):
        """
        This function deletes from the metadata db info about logged models with specified IDs. Those models will not appear in results 
        of the search_logged_models function then.
        """
        model_ids = ', '.join([f"'{id}'" for id in model_ids])

        self.postgresql.run_query(f"""
            DELETE
            FROM logged_models
            WHERE model_id in ({model_ids});
        """)

    
    

    def delete_registry_models_metadata(
        self
        ,model_uris: list[str] = None
        ,model_names_versions: list[str] = None
    ):
        """
        This function deletes from the metadata db info about models and their versions saved in the registry based on one of the below:
            - Model URIs
            - Model names and versions (this is a list of the format: ['model_name_1:version_1', 'model_name_2:version_2', ...])
        """
        # Construct the 'where' clause for the SQL query to identify model versions to delete. It has one of two possible formats:
        #   - where_clause = "where source in (model_uri_1, model_uri_2, ...)"
        #   - where_clause = "where (name = model_name_1 and version = model_version_1) or (name = model_name_2 and version = model_version_2) or ..."
        if model_uris is not None:
            model_uris = ', '.join([f"'{uri}'" for uri in model_uris])
            where_clause = f'where source in ({model_uris})'
        elif model_names_versions is not None:
            where_clause = ''
            for model_name_version in model_names_versions:
                model_name = model_name_version.split(':')[0]
                model_version = model_name_version.split(':')[1]
                if where_clause == '':
                    where_clause = f"where (name = '{model_name}' and version = '{model_version}')"
                else:
                    where_clause += f" or (name = '{model_name}' and version = '{model_version}')"
        else:
            raise Exception("You need to provide either the model_uris or model_names_versions argument.")

        # Delete info about model versions
        self.postgresql.run_query(f"DELETE FROM model_versions {where_clause}")

        # Delete info about those registered models, for which all the versions has been deleted
        self.postgresql.run_query(
            f"""
            DELETE FROM
                registered_models
            WHERE
                name in (
                    SELECT DISTINCT
                        rm.name
                    FROM
                        registered_models AS rm

                        LEFT JOIN model_versions AS mv
                            ON mv.name = rm.name
                    WHERE
                        mv.name IS NULL
                )
            """
        )