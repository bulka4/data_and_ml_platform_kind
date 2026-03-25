-- Set table name to "products"
{{ config(alias='products', tags=['source1']) }}

select
    1 as productID
    ,'product_1' as productName
    ,1 as price

union all select 2, 'product_2', 2