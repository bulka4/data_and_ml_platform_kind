-- Set table name to "clients"
{{ config(alias='clients', tags=['source1', 'source2']) }}

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