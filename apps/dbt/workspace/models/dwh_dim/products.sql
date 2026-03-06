with all_products as (
    select
        productID
        ,productName
        ,price
    from
        dwh_source1.products

    union all

    select
        productID
        ,productName
        ,price
    from
        dwh_source2.products
)

select distinct
    productID
    ,productName
    ,price
from
    all_products