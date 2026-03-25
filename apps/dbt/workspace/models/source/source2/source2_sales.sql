-- Set table name to "sales"
{{ config(alias='sales', tags=['source2']) }}

select
    1 as clientID
    ,1 as productID
    ,cast('2025-01-01' as date) as date
    ,5 as amount

union all select 1, 2, cast('2025-02-01' as date), 4
union all select 2, 1, cast('2025-03-01' as date), 2
union all select 3, 2, cast('2025-04-01' as date), 8
union all select 3, 2, cast('2025-05-01' as date), 4
union all select 3, 2, cast('2025-06-01' as date), 4