from sklearn.linear_model import LinearRegression
from sklearn.model_selection import train_test_split
import mlflow
import argparse

import sys, pathlib

sys.path.append(str(pathlib.Path(__file__).parent.parent.parent.resolve()))

from common.spark_class import Spark


print("Started training")

# -----------------------------
# Parse arguments
# -----------------------------
parser = argparse.ArgumentParser()
parser.add_argument("--fit_intercept", type=bool, required=True, help="The fit_intercept parameter for the sklearn.linear_model.LinearRegression model.")
parser.add_argument("--positive", type=bool, required=True, help="The positive parameter for the sklearn.linear_model.LinearRegression model.")
args = parser.parse_args()

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
    host='spark-thrift-server.spark.svc.cluster.local',   # DNS name of the Spark Thrift Server of the format: "<service-name>.<namespace>.svc.cluster.local"
    port=10000,
    auth='NOSASL'   # No authentication. Other options include 'LDAP', 'KERBEROS', etc.
)

df = spark.read_sql(query)
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
mlflow.sklearn.log_model(model, artifact_path="LR_model")
print("Finished training")
