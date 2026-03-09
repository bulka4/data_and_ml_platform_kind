mlflow run . \
    -e train \
    --env-manager local \
    --experiment-name=linear_regression_revenue \
    -P fit_intercept=True \
    -P positive=True \
    -P model_name=LR_model


mlflow run . \
    -e evaluate \
    --env-manager local \
    --experiment-name=linear_regression_revenue