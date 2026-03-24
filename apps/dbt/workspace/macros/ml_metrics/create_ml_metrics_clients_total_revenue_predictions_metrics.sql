/*This macro creates a table with a dummy record what is needed to build this table for the first time.*/
{% macro create_ml_metrics_clients_total_revenue_predictions_metrics() %}
    CREATE TABLE IF NOT EXISTS ml_metrics.clients_total_revenue_predictions_metrics AS
        SELECT
            add_months(max(month), -1) as month
            ,null as RMSE_1
            ,null as RMSE_2
            ,null as RMSE_3
            ,null as maxError
            ,null as modelURI
        FROM {{ ref('fact_clients_total_revenue_predictions') }}
{% endmacro %}