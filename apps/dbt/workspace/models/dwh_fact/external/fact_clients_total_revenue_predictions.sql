{{ config(alias="clients_total_revenue_predictions") }}

select
    null as clientID INT
    ,null as month
    ,null as predictedRevenue
    ,null as modelURI
where
    false