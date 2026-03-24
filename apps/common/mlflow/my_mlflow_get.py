"""
This is a class for getting information from the MLflow metadata database.
"""

import mlflow
from mlflow.tracking import MlflowClient


class MyMLflowGet():
    def __init__(
        self
    ):
        self.client = MlflowClient()


# ==================== Get models data ====================

    def find_latest_model(
        self
        ,experiment_name: str
    ):
        """
        Find the latest built model in the given experiment. This function returns the LoggedModel object.
        """
        experiment = mlflow.get_experiment_by_name(experiment_name)
        
        if experiment is None:
            raise ValueError(f"Experiment '{experiment_name}' not found")
                
        # Get info about models for the specified experiment
        latest_model = self.client.search_logged_models(
            experiment_ids=[experiment.experiment_id]
            ,order_by=[
                {"field_name": "creation_timestamp", "ascending": False}  # The latest model first
            ]
        )[0]

        return latest_model


    def get_the_best_model_uri(self, experiment_name: str, metrics: dict) -> str:
        """
        Get URI of the model with the best evaluation metrics. In order to use this function, the following assumptions must be met:
            - We have been evaluating a single model in a single MLflow run
            - Each run was logging evaluation metrics
            - Each run got assigned tag "evaluated_model_uri" indicating which model has been evaluated 
        
        Arguments:
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

        # Get data about the run which evaluated a model and got the best metrics
        runs_data = mlflow.search_runs(
            experiment_ids=[experiment.experiment_id],
            order_by=[f"metrics.{metric} {'DESC' if value=='highest' else 'ASC'}" for metric, value in metrics.items()],
            max_results=1
        )

        if runs_data.empty:
            raise ValueError("No runs found in experiment")

        if 'tags.evaluated_model_uri' not in runs_data.columns:
            raise Exception("There is no 'evaluated_model_uri' in runs tags.")

        # Get URI of the model which has been evaluated from evaluation run tags
        model_uri = runs_data.loc[0, 'tags.evaluated_model_uri']

        return model_uri





    # ==================== Get runs data ====================

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
    

    def get_experiment_run_ids(
        self
        ,experiment_name: str
    ) -> list[str]:
        """
        Get IDs of all the runs from the experiment with the specified name.
        """
        experiment = mlflow.get_experiment_by_name(experiment_name)

        if experiment is None:
            raise ValueError(f"Experiment '{experiment_name}' not found")
        
        runs = mlflow.search_runs(
            experiment_ids=[experiment.experiment_id]
        )

        return runs['run_id'].values


    def get_registered_model_names(
        self
        ,experiment_name: str = None
        ,run_id: str = None
    ) -> list[str]:
        """
        Get names of all the registered models from either the entire experiment or only a specific run.
        """
        if experiment_name != None:
            run_ids = self.get_experiment_run_ids(experiment_name)
        elif run_id != None:
            run_ids = [run_id]
        else:
            raise Exception("You need to provide either the experiment_name or run_id argument.")
        
        model_names = []
        for run_id in run_ids:
            found_model = self.client.search_model_versions(filter_string=f"run_id='{run_id}'")
            if len(found_model) > 0:
                model_names.append(found_model[0].name)

        return model_names