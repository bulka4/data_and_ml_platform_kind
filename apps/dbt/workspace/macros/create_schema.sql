{% macro create_iceberg_schema(schema_name) %}
  {% set sql %}
    CREATE SCHEMA IF NOT EXISTS {{ schema_name }}
  {% endset %}

  {{ log("Executing: " ~ sql, info=True) }}

  {% do run_query(sql) %}
{% endmacro %}