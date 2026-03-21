-- Set table name to "customers_total_revenue"
{{ config(alias='customers_total_revenue') }}

select
    clientID
    ,concat(date_format(date, 'yyyy-MM'), '-01') as month
    ,sum(totalPrice) as revenue
from
    {{ ref('fact_sales') }}
group by
    clientID
    ,concat(date_format(date, 'yyyy-MM'), '-01')