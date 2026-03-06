select
    clientID
    ,productID
    ,date
    ,amount
    ,p.price * amount as totalPrice
from
    dwh_raw.sales as s

    left join dwh_dim.products as p
        on p.productID = s.productID