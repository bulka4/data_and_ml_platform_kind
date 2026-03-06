-- Set table name to "customersTotalRevenue"
{{ config(alias='customersTotalRevenue') }}

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