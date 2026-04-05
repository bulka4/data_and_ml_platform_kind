# Bash commands for running MLflow projects

# Use the env-manager = local parameter to run MLflow locally (in the pod where we run this command, there is everything prepared to run MLflow)

# Training a model
mlflow run . \
    -e train \
    --env-manager local \
    --experiment-name=linear_regression_revenue \
    -P start_date="2025-01-01" \
    -P end_date="2025-06-01" \
    -P fit_intercept=True \
    -P positive=True \
    -P model_name=LR_model

# Evaluating the latest created model from the experiment where we run this entrypoint
mlflow run . \
    -e eval_latest \
    --env-manager local \
    --experiment-name=linear_regression_revenue

# Evaluating all models from the experiment where we run this entrypoint
mlflow run . \
    -e eval_all \
    --env-manager local \
    --experiment-name=linear_regression_revenue \
    -P start_date="2025-05-01" \
    -P end_date="2025-06-01"