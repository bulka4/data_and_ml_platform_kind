"""
Functions related to MLflow.
"""

import mlflow
from mlflow.tracking import MlflowClient
import pandas as pd
import numpy as np


class MyMLflow():
    def __init__(
        self
    ):
        self.client = MlflowClient()


    def load_model(
        self
        ,experiment_name: str
        ,run_id: str
        ,model_name=None
    ):
        """
        Load the model from the specified experiment and run.
        Arguments:
            - run_id - ID of the run, can be obtained using for example get_latest_run_id function from this class or mlflow.search_runs().
            - model_name - If there are multiple models for the given run, this argument specifies name of the model to load. It is not needed
                    if there is only one model for the run.
        """
        experiment = mlflow.get_experiment_by_name(experiment_name)
        
        if experiment is None:
            raise ValueError(f"Experiment '{experiment_name}' not found")
                
        # Get info about models
        if model_name == None:
            # Get info about models for the specified experiment and run
            models = self.client.search_logged_models(
                experiment_ids=[experiment.experiment_id]
                ,filter_string=f"source_run_id='{run_id}'"
            )
        else:
            # Get info about models for the specified experiment, run and model name
            models = self.client.search_logged_models(
                experiment_ids=[experiment.experiment_id]
                ,filter_string=f"source_run_id='{run_id}' AND name='{model_name}'"
            )

        # Handle exceptions
        if not models:
            raise ValueError(f"No model found for run {run_id}")
        elif len(models) > 1:
            if model_name == None:
                raise Warning("There are multiple models for the specified run. You might want to use the model_name argument to specify which model to load.")
            else:
                raise Warning("There are multiple models for the specified run and model name.")
        elif len(models) == 0:
            if model_name == None:
                raise Exception("There are no models for the specified run.")
            else:
                raise Exception("There are no models for the specified run and model name.")
        else:
            model = models[0]

        return mlflow.sklearn.load_model(model.model_uri)


    def load_latest_model(
        self
        ,experiment_name: str
    ):
        """
        Load the latest model from the given experiment. We use the creation_timestamp field from info about models returned by the
        search_logged_models function to determine the latest model.
        """
        experiment = mlflow.get_experiment_by_name(experiment_name)
        
        if experiment is None:
            raise ValueError(f"Experiment '{experiment_name}' not found")
                
        # Get info about models for the specified experiment
        models = self.client.search_logged_models(
            experiment_ids=[experiment.experiment_id]
        )

        # Sort models based on the creation_timestamp field to get the latest one
        latest_model = sorted(models, key=lambda model: model.creation_timestamp, reverse=True)[0]

        return mlflow.sklearn.load_model(latest_model.model_uri)


    def get_latest_run_id(self, experiment_name: str) -> str:
        """
        Returns the run ID of the most recent run in the given experiment.
        """
        # Get experiment object by name
        experiment = mlflow.get_experiment_by_name(experiment_name)
        if experiment is None:
            raise ValueError(f"Experiment '{experiment_name}' not found")
        
        # Search runs in descending order of start time
        runs = mlflow.search_runs(
            experiment_ids=[experiment.experiment_id],
            order_by=["start_time DESC"],
            max_results=1
        )
        
        if runs.empty:
            raise ValueError(f"No runs found in experiment '{experiment_name}'")
        
        # Return the run ID of the latest run
        return runs.loc[0, "run_id"]


    def get_the_best_run(self, experiment_name: str, metrics: dict) -> str:
        """
        Get ID of the run with the best metrics. Arguments:
            - metrics - a dictionary specifying names of metrics and whether we want to get a run with the highest or lowest values of those metrics.
                It is of the following format:
                {
                    'metric_1_name': 'highest'   # Get the run with highest value of this metric
                    ,'metric_2_name': 'lowest'   # Get the run with the lowest value of this metric
                }
        """
        # Check whether there are invalid parameters (different names than 'highest' and 'lowest' in the metrics argument).

        # Get invalid values from the metrics matrix, that is values different than 'highest' and 'lowest' in the second column of that matrix
        invalid = [value for metric, value in metrics.items() if value not in ["highest", "lowest"]]

        if invalid:
            raise Exception("In the metrics parameter we can only provide values 'highest' and 'lowest' for each metric.")
        
        experiment = mlflow.get_experiment_by_name(experiment_name)

        if experiment is None:
            raise ValueError(f"Experiment '{experiment_name}' not found")

        runs = mlflow.search_runs(
            experiment_ids=[experiment.experiment_id],
            order_by=[f"metrics.{metric} {'DESC' if value=='highest' else 'ASC'}" for metric, value in metrics.items()],
            max_results=1
        )

        if runs.empty:
            raise ValueError("No runs found in experiment")

        return runs.loc[0, "run_id"]


    def delete_run(
        self
        ,run_id: str
        ,experiment_name: str
    ) -> list:
        """
        Soft delete of a run. It doesn't delete any artifacts but the run will not be visible in results of functions such as mlflow.search_runs()
        unless we use "run_view_type=mlflow.entities.ViewType.ALL".

        This function returns paths where models and other artifacts created in this run are saved, so we can delete them manually if we want.

        Arguments:
            - run_id - ID of the run to delete
            - experiment_name - Name of the experiment to which that run belongs
        """
        self.client.delete_run(run_id)

        experiment = mlflow.get_experiment_by_name(experiment_name)

        if experiment is None:
            raise ValueError(f"Experiment '{experiment_name}' not found")
        
        # Get logged models and run data for the given experiment and run ID
        models = self.client.search_logged_models(
            experiment_ids=[experiment.experiment_id]
            ,filter_string=f"source_run_id='{run_id}'"
        )

        run = mlflow.get_run(run_id)

        # Return paths where models and artifacts are saved
        return [model.artifact_location for model in models] + [run.info.artifact_uri]


    def delete_experiment(
        self
        ,experiment_name: str
    ):
        """
        Perform a soft delete of an experiment. It will disappear from the UI and results of mlflow.search_experiments() but we can still see it using
        mlflow.search_experiments(view_type=2) and restore it using self.client.restore_experiment(experiment_id).

        This function returns paths where models and other artifacts created in this run are saved, so we can delete them manually if we want.
        """
        experiment = mlflow.get_experiment_by_name(experiment_name)

        if experiment is None:
            raise ValueError(f"Experiment '{experiment_name}' not found")

        mlflow.delete_experiment(experiment.experiment_id)

        # Get logged models and runs data for the given experiment
        models = self.client.search_logged_models(experiment_ids=[experiment.experiment_id])
        runs = mlflow.search_runs(experiment_ids=[experiment.experiment_id])

        # Return paths where models and artifacts are saved
        return np.concatenate(([model.artifact_location for model in models], runs['artifact_uri'].values))