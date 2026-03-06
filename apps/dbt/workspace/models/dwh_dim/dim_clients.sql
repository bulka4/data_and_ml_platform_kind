-- Set table name to "clients"
{{ config(alias='clients') }}

with all_clients as (
    select
        clientID
        ,clientName
        ,clientCountry
    from
        {{ ref('source1_clients') }}

    union all

    select
        clientID
        ,clientName
        ,clientCountry
    from
        {{ ref('source2_clients') }}
)

select distinct
    clientID
    ,clientName
    ,clientCountry
from
    all_clients