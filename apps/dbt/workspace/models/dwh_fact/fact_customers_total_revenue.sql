-- Set table name to "customers_total_revenue"
{{ config(alias='customers_total_revenue') }}

select
    clientID
    ,sum(totalPrice) as revenue
from
    {{ ref('fact_sales') }}
where
    year(date) = 2025
    and month(date) = 1
group by
    clientID