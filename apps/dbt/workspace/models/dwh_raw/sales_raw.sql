-- Set table name to "sales"
{{ config(alias='sales') }}

select
    clientID
    ,productID
    ,date
    ,amount
from
    dwh_source1.sales

union all

select
    clientID
    ,productID
    ,date
    ,amount
from
    dwh_source2.sales