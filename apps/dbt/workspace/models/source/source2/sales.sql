select
    1 as clientID
    ,1 as productID
    ,cast('2025-01-01' as date) as date
    ,5 as amount

union all select 1, 2, cast('2025-01-02' as date), 4
union all select 2, 1, cast('2025-01-03' as date), 2
union all select 3, 2, cast('2025-01-04' as date), 8