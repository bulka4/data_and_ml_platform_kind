-- Set table name to "sales"
{{ config(alias='sales', tags=['source1', 'source2']) }}

select
    clientID
    ,productID
    ,date
    ,amount
from
    {{ ref('source1_sales') }}

union all

select
    clientID
    ,productID
    ,date
    ,amount
from
    {{ ref('source2_sales') }}