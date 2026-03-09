from sklearn.linear_model import LinearRegression
from sklearn.model_selection import train_test_split
import mlflow
import argparse

import os, sys, pathlib

# Add apps folder to the sys.path so we can import from apps/common
sys.path.append(str(pathlib.Path(__file__).parent.parent.parent.resolve()))

from common.spark_class import Spark


print("Started training")

# -----------------------------
# Parse arguments
# -----------------------------
parser = argparse.ArgumentParser()
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
    ,help="Model name used to save the model."
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

query = """
SELECT
    clientID
    ,revenue
FROM
    dwh_fact.customersTotalRevenue
LIMIT 10
"""

spark = Spark(
    host=spark_host,   # DNS name of the Spark Thrift Server of the format: "<service-name>.<namespace>.svc.cluster.local"
    port=10000, 
    auth='NONE' # No authentication. Other options include 'LDAP', 'KERBEROS', etc.
)

df = spark.read_query(query)
x = df[['clientID']]
y = df['revenue']

# -----------------------------
# Split into train/test
# -----------------------------
X_train, X_test, y_train, y_test = train_test_split(x, y, test_size=0.2, random_state=42)

# -----------------------------
# Train Lasso Regression
# -----------------------------
model = LinearRegression(
    fit_intercept=args.fit_intercept
    ,positive=args.positive
)

# Train model
model.fit(X_train, y_train)

# -----------------------------
# Save model in artifact store
# -----------------------------
    
# mlflow.set_experiment("linear_regression")

# Start a run and assign the model to it
with mlflow.start_run() as run:
    mlflow.sklearn.log_model(model, name=args.model_name)
print("Finished training")