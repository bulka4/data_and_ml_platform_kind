# Resource Group
module resource_group {
    source = "./modules/resource_group"
    name     = var.resource_group_name
    location = var.location
}

# Storage account for system files:
#   - Airflow logs
#   - Code pulled by git-sync
locals {
  system_files_sa_name = "systemfilesbulka"
}

module "system_files_sa" {
  source = "./modules/storage_account"
  resource_group_name = module.resource_group.name
  resource_group_location = module.resource_group.location
  storage_account_name = local.system_files_sa_name
}


# Container for Airflow logs
locals {
  airflow_logs_container_name = "airflow-logs"
}

module "airflow_logs_container" {
  source = "./modules/sa_container"
  name = local.airflow_logs_container_name
  storage_account_name = module.system_files_sa.name
}

# File share for code pulled by git-sync
module "git_sync_fs" {
  source = "./modules/sa_file_share"
  name = "git-sync"
  storage_account_name = module.system_files_sa.name
}



# Storage account for containers:
#   - DWH - Data warehouse data
#   - mlflow - MLflow artifacts
module "dwh_sa" {
  source                  = "./modules/storage_account"
  resource_group_name     = module.resource_group.name
  resource_group_location = module.resource_group.location
  storage_account_name    = "dwhbulka"
  gen2                    = true
}

# Container for DWH (data warehouse). We will keep there data used for Spark calculations.
module "dwh_container" {
  source = "./modules/sa_container"
  name = "dwh"
  storage_account_name = module.dwh_sa.name
}

# Container for MLflow artifacts
module "mlflow_container" {
  source = "./modules/sa_container"
  name = "mlflow"
  storage_account_name = module.dwh_sa.name
}

# Service Principal for authentication. It is going to have assigned the following roles and scopes:
# - Role 'Storage Blob Data Contributor' - Enable saving data in a Storage Accounts (both with system files and the DWH one)

module "service_principal" {
  source = "./modules/service_principal"
  service_principal_display_name = "rag_workflow"
  role_assignments = [
    {role = "Storage Blob Data Contributor", scope = module.system_files_sa.id}
    {role = "Storage Blob Data Contributor", scope = module.dwh_sa.id}
  ]
}



# Create files content which will be saved on the localhost:
# - Dockerfile for creating an image for interacting with AKS
# - values.yaml files for Helm charts
locals {
  # values.yaml for the Airflow Helm chart
  airflow_chart_values = templatefile("template_files/helm_charts/values-airflow.yaml", {
    acr_url             = module.acr.url
    airflow_image_name  = local.airflow_image_name
    airflow_image_tag   = local.airflow_image_tag

    airflow_kubernetes_namespace = "airflow"
    
    airflow_logs_sa_name        = local.system_files_sa_name        # Name of the Storage Account where logs will be saved
    airflow_logs_container_name = local.airflow_logs_container_name # Name of the container where logs will be saved
    airflow_dags_fs_name        = module.git_sync_fs.name               # Name of the File share where DAGs code will be saved

    repo_url  = "https://github.com/bulka4/data_and_ml_platform.git"  # URL of the repository with code with Airflow DAGs (https://github.com/<org-name>/<repo-name>.git)
    repo_name = "data_and_ml_platform.git"                            # Name of the repo (<repo-name>.git)
    branch    = "main"                                                # Branch with the code to run
    dags_folder_path = "apps/airflow/dags"                            # Path to the folder with dags within the repo

    storage_account_secret = "airflow-azure-blob" # Name of the secret with credentials for accessing Storage Account (to create a connection)
    acr_secret_name = "acr-secret"
  })


  # values.yaml for the Spark Thrift Server Helm chart
  thrift_server_values = templatefile("template_files/helm_charts/values-thrift-server.yaml", {
    spark_image_name = local.spark_image_name

    sa_name           = module.dwh_sa.name        # Name of the Storage Account where Hive warehouse data used for Spark calculations will be saved
    sa_container_name = module.dwh_container.name # Name of the container where Hive warehouse data used for Spark calculations will be saved
  })


  # values.yaml for the Hive Helm chart
  hive_values = templatefile("template_files/helm_charts/values-hive.yaml", {
    sa_name           = module.dwh_sa.name        # Name of the Storage Account where data used for Spark calculations will be saved
    sa_container_name = module.dwh_container.name # Name of the container in the Storage Account where data used for Spark calculations will be saved
  })

  # values.yaml for the MLflow setup Helm chart
  mlflow_setup_values = templatefile("template_files/helm_charts/values-mlflow-setup.yaml", {
    mlflow_storage_account_name       = module.dwh_sa.name           # Storage Account for storing artifacts
    mlflow_container                  = module.mlflow_container.name # Container for storing artifacts
  })

  # create_k8s_secrets.sh script for creating Kubernetes secrets
  create_k8s_secrets = templatefile("template_files/create_k8s_secrets_template.sh", {
    system_files_sa     = module.system_files_sa.name                     # Name of the Storage Account used for Airflow logs
    system_files_sa_key = module.system_files_sa.primary_access_key       # Access key to the Storage Account
    
    dwh_sa              = module.dwh_sa.name                              # Name of the Storage Account used for Spark data warehouse data
    dwh_sa_access_key   = module.dwh_sa.primary_access_key                # Access key to the Storage Account
  })
}


# Save files on the localhost
resource "local_file" "local_files" {
  # each.key - content to save in a file
  # each.value - path where to save a file
  for_each = {
    1 = {content = local.airflow_chart_values, path = "../helm_charts/airflow/values.yaml"}
    2 = {content = local.thrift_server_values, path = "../helm_charts/spark_thrift_server/values.yaml"}
    3 = {content = local.hive_values, path = "../helm_charts/hive_metastore/values.yaml"}
    4 = {content = local.mlflow_setup_values, path = "../helm_charts/mlflow_setup/values.yaml"}
    5 = {content = local.create_k8s_secrets, path = "../create_k8s_secrets.sh"}
  }

  content = each.value.content
  filename = each.value.path
}


# Get info about the current client to get subscription ID
data "azurerm_client_config" "current" {}