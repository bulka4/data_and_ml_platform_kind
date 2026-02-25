{{- define "mlflow-job.fullname" -}}
{{- printf "%s-mlflow-job" .Release.Name | trunc 63 | trimSuffix "-" -}}
{{- end -}}