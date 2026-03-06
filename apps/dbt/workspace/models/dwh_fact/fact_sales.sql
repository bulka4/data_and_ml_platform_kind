-- Set table name to "sales"
{{ config(alias='sales') }}

select
    clientID
    ,productID
    ,date
    ,amount
    ,p.price * amount as totalPrice
from
    
    {{ ref('raw_sales') }} as s

    left join {{ ref('dim_products') }} as p
        on p.productID = s.productID