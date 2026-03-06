-- Set table name to "sales"
{{ config(alias='sales') }}

select
    s.clientID
    ,s.productID
    ,s.date
    ,s.amount
    ,p.price * s.amount as totalPrice
from
    
    {{ ref('raw_sales') }} as s

    left join {{ ref('dim_products') }} as p
        on p.productID = s.productID