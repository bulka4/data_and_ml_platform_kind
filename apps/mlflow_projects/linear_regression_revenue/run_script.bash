# Bash commands for running MLflow projects

mlflow run . \
    -e train \
    --env-manager local \
    --experiment-name=linear_regression_revenue \
    -P fit_intercept=True \
    -P positive=True \
    -P model_name=LR_model


mlflow run . \
    -e eval_latest \
    --env-manager local \
    --experiment-name=linear_regression_revenue


mlflow run . \
    -e eval_all \
    --env-manager local \
    --experiment-name=linear_regression_revenue