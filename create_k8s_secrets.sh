# user, password and database we create in PostgreSQL which will be used by Airflow
POSTGRES_USER=airflow
POSTGRES_PASSWORD=airflow
POSTGRES_DB=airflow

AIRFLOW_POSTGRES_SECRET=airflow-postgres    # secret used for the PostgreSQL deployment
AIRFLOW_POSTGRES_CONNECTION_SECRET=airflow-postgres-connection  # secret used by Airflow to connect to PostgreSQL
POSTGRES_DNS=airflow-postgres   # DNS name of PostgreSQL (name of the kubernetes service we will create for Postgres deployment)



# Create namespaces
for ns in "airflow" "spark" "mlflow"; do
	kubectl create namespace $ns
done


# ================ Airflow ================

# Create a secret used by Airflow to connect to PostgreSQL metadata db
kubectl create secret generic airflow-postgres-connection \
	--from-literal=connection=postgresql://${POSTGRES_USER}:${POSTGRES_PASSWORD}@${POSTGRES_DNS}:5432/${POSTGRES_DB} \
	-n airflow


# Create a secret used by PostgreSQL deployment (to create a user and database used by Airflow)
kubectl create secret generic airflow-postgres \
	--from-literal=postgres_user=${POSTGRES_USER} \
	--from-literal=postgres_password=${POSTGRES_PASSWORD} \
	--from-literal=postgres_database=${POSTGRES_DB} \
	-n airflow





# ================ Spark ================

# Secret for Hive Metastore for accessing PostgreSQL metadata db:
kubectl create secret generic hive-metastore-db-secret \
  --from-literal=hive-password=hivepassword \
  --from-literal=postgres-password=adminpassword \
  -n spark

# Service Principal's credentials which will be used in the `spark-defaults.conf`
kubectl create secret generic adls-sp-secret \
  --from-literal=client-id=XXXX \
  --from-literal=client-secret=XXXX \
  --from-literal=tenant-id=XXXX \
  --from-literal=storage-account=
  -n spark