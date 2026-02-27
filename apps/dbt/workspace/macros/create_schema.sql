{% macro create_iceberg_schema(schema_name) %}
CREATE SCHEMA IF NOT EXISTS {{ schema_name }}
{% endmacro %}