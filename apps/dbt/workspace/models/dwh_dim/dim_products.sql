-- Set table name to "products"
{{ config(alias='products') }}

with all_products as (
    select
        productID
        ,productName
        ,price
    from
        {{ ref('source1_products') }}

    union all

    select
        productID
        ,productName
        ,price
    from
        {{ ref('source2_products') }}
)

select distinct
    productID
    ,productName
    ,price
from
    all_products