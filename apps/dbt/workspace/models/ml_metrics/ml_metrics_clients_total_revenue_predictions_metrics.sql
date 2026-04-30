/*
This model adds to the target table one record with metrics calculated for the latest month from the source table clients_total_revenue. It needs to be ran 
every month in order to have metrics calculated for every month. Otherwise, previous months will be skipped.

It uses predictions made only by the latest model. For example, if two and three months ago a different model was used, then metrics for those months will
be NULL.

Also, this model needs to be ran after making predictions, so we have data about them (if it runs before making predictions, it will not
add any records, so nothing wrong will happen).
*/

{{ config(
    alias="clients_total_revenue_predictions_metrics"
    ,materialized="incremental"
    ,tags=['ml_metrics']
) }}

-- Get URI of the latest model used
with latest_model_uri as (
    select modelURI
    from {{ source('python', 'clients_total_revenue_predictions') }}
    order by month desc
    limit 1
)

-- Get predictions data for the last 3 months. If model used for some of those months was different than the latest model, then ignore those months
-- (set prediction value to NULL)
,predictions as (
    select
        clientID
        ,month
        ,case
            when latest_model_uri.modelURI != pred.modelURI
            then null
            else predictedRevenue
        end as predictedRevenue
    from
        {{ source('python', 'clients_total_revenue_predictions') }} as pred

        cross join latest_model_uri
    where
        month > (select add_months(max(month), -3) from {{ source('python', 'clients_total_revenue_predictions') }})
)

-- RMSE for the last 1 month (those predictions were made using the latest model so we don't need to use the 'predictions' CTE)
,rmse_1 as (
    select
        max(rev.month) as month -- Month for which the metrics are calculated
        ,sqrt(avg(power(rev.revenue - pred.predictedRevenue, 2))) as RMSE_1
    from
        {{ ref('fact_clients_total_revenue') }} as rev

        left join {{ source('python', 'clients_total_revenue_predictions') }} as pred
            on pred.clientID = rev.clientID
            and pred.month = rev.month
    where
        rev.month >= (select max(month) from {{ ref('fact_clients_total_revenue') }})
)

-- RMSE for the last 2 months
,rmse_2 as (
    select
        sqrt(avg(power(rev.revenue - pred.predictedRevenue, 2))) as RMSE_2
    from
        {{ ref('fact_clients_total_revenue') }} as rev

        left join predictions as pred
            on pred.clientID = rev.clientID
            and pred.month = rev.month
    where
        rev.month >= (select add_months(max(month), -1) from {{ ref('fact_clients_total_revenue') }})
)

-- RMSE for the last 3 months
,rmse_3 as (
    select
        sqrt(avg(power(rev.revenue - pred.predictedRevenue, 2))) as RMSE_3
    from
        {{ ref('fact_clients_total_revenue') }} as rev

        left join predictions as pred
            on pred.clientID = rev.clientID
            and pred.month = rev.month
    where
        rev.month >= (select add_months(max(month), -2) from {{ ref('fact_clients_total_revenue') }})
)

-- max error for the last month
,max_error as (
    select
        max(abs(rev.revenue - pred.predictedRevenue)) as maxErrorLastMonth
    from
        {{ ref('fact_clients_total_revenue') }} as rev

        left join {{ source('python', 'clients_total_revenue_predictions') }} as pred
            on pred.clientID = rev.clientID
            and pred.month = rev.month
    where
        rev.month >= (select max(month) from {{ ref('fact_clients_total_revenue') }})
)

select
    rmse_1.month
    ,RMSE_1
    ,RMSE_2
    ,RMSE_3
    ,maxErrorLastMonth
    ,latest_model_uri.modelURI
from
    rmse_1
    cross join rmse_2
    cross join rmse_3
    cross join max_error
    cross join latest_model_uri
-- If there is no metric for the last month, there will be also no metrics for the previous months, so there are no metrics to be added (don't
-- add a record to the target table with only NULLs)
where
    RMSE_1 is not null