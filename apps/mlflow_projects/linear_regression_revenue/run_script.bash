# Bash commands for running MLflow projects

# Training a model
mlflow run . \
    -e train \
    --env-manager local \
    --experiment-name=linear_regression_revenue \
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
    --experiment-name=linear_regression_revenue