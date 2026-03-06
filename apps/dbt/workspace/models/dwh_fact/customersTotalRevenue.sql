select
    clientID
    ,sum(totalPrice) as revenue
from
    dwh_fact.sales
where
    year(date) = 2025
    and month(date) = 1