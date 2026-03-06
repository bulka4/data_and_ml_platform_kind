-- Set table name to "clients"
{{ config(alias='clients') }}

select
    1 as clientID
    ,'client_1' as clientName
    ,'USA' as clientCountry

union all select 2, 'client_2', 'France'
union all select 3, 'client_3', 'Australia'