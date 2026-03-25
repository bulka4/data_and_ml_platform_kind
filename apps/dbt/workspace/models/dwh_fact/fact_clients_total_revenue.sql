-- Set table name to "clients_total_revenue"
{{ config(alias='clients_total_revenue', tags=['source1', 'source2']) }}

select
    clientID
    ,concat(date_format(date, 'yyyy-MM'), '-01') as month
    ,sum(totalPrice) as revenue
from
    {{ ref('fact_sales') }}
group by
    clientID
    ,concat(date_format(date, 'yyyy-MM'), '-01')