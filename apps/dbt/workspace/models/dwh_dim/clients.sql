with all_clients as (
    select
        clientID
        ,clientName
        ,clientCountry
    from
        dwh_source1.clients

    union all

    select
        clientID
        ,clientName
        ,clientCountry
    from
        dwh_source2.clients
)

select distinct
    clientID
    ,clientName
    ,clientCountry
from
    all_clients