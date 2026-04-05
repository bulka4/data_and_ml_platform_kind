"""
This is a script for training and evaluating a linear regression model.

It saves tags:
    - created_model_uri - URI of the trained model

and metrics from evaluation of the created model:
    - mse
    - r2
"""

from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_squared_error, r2_score
import mlflow
import argparse
import math

import os, sys, pathlib

# Add "apps" folder to the sys.path so we can import from "apps/common"
sys.path.append(str(pathlib.Path(__file__).parent.parent.parent.resolve()))

from common.mlflow.my_mlflow import MyMLflow
from common.spark_thrift_class import SparkThrift


print("Started training")
my_mlflow = MyMLflow()

# -----------------------------
# Parse arguments
# -----------------------------
parser = argparse.ArgumentParser()
parser.add_argument(
    "--start_date"
    ,type=str
    ,help="We select data for training for the timeframe between the start_date and end_date perameters."
)
parser.add_argument(
    "--end_date"
    ,type=str
    ,help="We select data for training for the timeframe between the start_date and end_date perameters."
)
parser.add_argument(
    "--fit_intercept"
    ,type=bool
    ,default=True
    ,help="The fit_intercept parameter for the sklearn.linear_model.LinearRegression model."
)
parser.add_argument(
    "--positive"
    ,type=bool
    ,default=True
    ,help="The positive parameter for the sklearn.linear_model.LinearRegression model."
)
parser.add_argument(
    "--model_name"
    ,type=str
    ,required=True
    ,help="Model name used to save the model (not in the registry but in logged models)."
)
args = parser.parse_args()



# -----------------------------
# Get environment variables values
# -----------------------------
# DNS name of the Spark Thrift Server to connect to (to get data from it for training models).
spark_host = os.getenv('SPARK_THRIFT_SERVER_DNS')



# -----------------------------
# Get data for training
# -----------------------------

spark = SparkThrift(
    host=spark_host,   # DNS name of the Spark Thrift Server of the format: "<service-name>.<namespace>.svc.cluster.local"
    port=10000, 
    auth='NONE' # No authentication. Other options include 'LDAP', 'KERBEROS', etc.
)

# Take data for training from a specific timeframe
query = f"""
SELECT
    next.clientID
    ,previous.revenue as revenueLastMonth
    ,next.revenue
FROM
    dwh_fact.clients_total_revenue as previous

    join dwh_fact.clients_total_revenue as next
        on next.clientID = previous.clientID
        and next.month = add_months(previous.month, 1)
WHERE
    previous.month >= '{args.start_date}'
    and previous.month <= '{args.end_date}'
-- Order data so we can split it into train/test datasets by taking the latest data for testing
ORDER BY
    previous.month desc
"""

df = spark.read_query(query)
x = df[['clientID', 'revenueLastMonth']]
y = df['revenue']



# -----------------------------
# Split into train/test
# -----------------------------

# How many percent of sample to take for the test dataset
test_size = 0.34    # 1/3 of the dataset, to include at least 2 samples in the test dataset, so we can calculate R^2 metric
no_samples = len(df)

# Take the latest data for testing dataset and the rest for the training.
# Top rows up until the row with the index given by the split_idx goes to the training dataset, the rest of bottom rows go to the test dataset
# (because data is sorted, the latest months are at the bottom)
split_idx = math.floor((1 - test_size) * no_samples)

x_train = x.iloc[ : split_idx]
y_train = y.iloc[ : split_idx]
x_test  = x.iloc[split_idx : ]
y_test  = y.iloc[split_idx : ]



# -----------------------------
# Train the model
# -----------------------------
model = LinearRegression(
    fit_intercept=args.fit_intercept
    ,positive=args.positive
)

model.fit(x_train, y_train)



# -----------------------------
# Evaluate the model
# -----------------------------
y_pred = model.predict(x_test)
mse = mean_squared_error(y_test, y_pred)
r2 = r2_score(y_test, y_pred)



# -----------------------------
# Save the model and metrics in the artifact store
# -----------------------------

# Start a run and assign the model to it (or assign it to the run already started with 'mlflow run' command)
with mlflow.start_run() as run:
    model_info = mlflow.sklearn.log_model(model, name=args.model_name)

    mlflow.set_tag("created_model_uri", model_info.model_uri)
    mlflow.log_metric("mse", mse)
    mlflow.log_metric("r2", r2)
print("Finished training")