/*This code adds to the target table one record with metrics calculated for the latest month from the source table clients_total_revenue.*/

-- If the target table doesn't exist yet, use pre-hook to create a dummy record with a proper date which is a month earlier than the latest month
-- in the clients_total_revenue table.
-- Thanks to that, the oldMonth column from the "month" CTE is equal to this month and the condition 
-- "rev.month > (select oldMonth from month)" includes only the latest month.
{{ config(
    alias="clients_total_revenue_predictions_metrics"
    ,materialized="incremental"
    ,tags=['ml_metrics']
) }}

-- Take the latest months from the current target table (with metrics) and source table (with predictions)
with month as (
    select
        t.oldMonth
        ,s.newMonth
    from
        -- If this target table which we are creating already exists, then select the latest month from it. Otherwise, select the second latest date
        -- from the fact_clients_total_revenue_predictions.
        {% if is_incremental() %}
            (select max(month) as oldMonth from {{ this }}) as t
        {% else %}
            (select add_months(max(month), -1) as oldMonth from {{ ref('fact_clients_total_revenue_predictions') }}) as t
        {% endif %}
        cross join (select max(month) as newMonth from {{ ref('fact_clients_total_revenue_predictions') }}) as s
)

-- Get URI of the latest model used
,latest_model_uri as (
    select modelURI
    from {{ ref('fact_clients_total_revenue_predictions') }}
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
        {{ ref('fact_clients_total_revenue_predictions') }} as pred

        cross join latest_model_uri
    where
        month > (select date_add(max(month), -3) from {{ ref('fact_clients_total_revenue_predictions') }})
)

-- RMSE for the last 1 month (those predictions were made using the latest model so we don't need to use the 'predictions' CTE)
,rmse_1 as (
    select
        max(rev.month) as month
        ,sqrt(avg(power(rev.revenue - pred.predictedRevenue, 2))) as RMSE_1
    from
        {{ ref('fact_clients_total_revenue') }} as rev

        left join {{ ref('fact_clients_total_revenue_predictions') }} as pred
            on pred.clientID = rev.clientID
            and pred.month = rev.month
    where
        rev.month > (select oldMonth from month)
)

-- RMSE for the last 2 months
,rmse_2 as (
    select
        max(rev.month) as month
        ,sqrt(avg(power(rev.revenue - pred.predictedRevenue, 2))) as RMSE_2
    from
        {{ ref('fact_clients_total_revenue') }} as rev

        left join predictions as pred
            on pred.clientID = rev.clientID
            and pred.month = rev.month
    where
        rev.month > add_months((select oldMonth from month), -1)
)

-- RMSE for the last 3 months
,rmse_3 as (
    select
        max(rev.month) as month
        ,sqrt(avg(power(rev.revenue - pred.predictedRevenue, 2))) as RMSE_3
    from
        {{ ref('fact_clients_total_revenue') }} as rev

        left join predictions as pred
            on pred.clientID = rev.clientID
            and pred.month = rev.month
    where
        rev.month > add_months((select oldMonth from month), -2)
)

-- max error for the last month
,max_error as (
    select
        max(rev.month) as month
        ,max(abs(rev.revenue - pred.predictedRevenue)) as maxErrorLastMonth
    from
        {{ ref('fact_clients_total_revenue') }} as rev

        left join {{ ref('fact_clients_total_revenue_predictions') }} as pred
            on pred.clientID = rev.clientID
            and pred.month = rev.month
    where
        rev.month > (select oldMonth from month)
)

select
    month.newMonth as month
    ,RMSE_1
    ,RMSE_2
    ,RMSE_3
    ,maxErrorLastMonth
    ,latest_model_uri.modelURI
from
    month
    -- Use the inner join, so in case there is no data in rmse_1 and other tables, result of this select statement is empty (so we don't add
    -- rows to the target table)
    join rmse_1 on month.newMonth = rmse_1.month
    join rmse_2 on month.newMonth = rmse_2.month
    join rmse_3 on month.newMonth = rmse_3.month
    join max_error on month.newMonth = max_error.month
    cross join latest_model_uri