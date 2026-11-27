-- Calendar 
-- Step 1: Clear existing data from the hardoi_event_calendar table (optional)
TRUNCATE TABLE raw_source_data.hardoi_event_calendar;

-- Step 2: Insert dates from up_calendar into hardoi_event_calendar
INSERT INTO raw_source_data.hardoi_event_calendar (date)
SELECT date
FROM raw_source_data.up_calendar;

select * from raw_source_data.hardoi_event_calendar where is_event = 1;

UPDATE raw_source_data.hardoi_event_calendar
SET 
    is_event = 1,
    event_name = CASE
        WHEN date = '2023-12-01' THEN 'Hardoi Mela Mahotsav 2024'
        WHEN date = '2024-04-28' THEN 'Brainobrain Zonal Fest 2024'
        WHEN date = '2024-06-04' THEN 'Expansion of Distillery Capacity'
        ELSE event_name
    END
WHERE date IN ('2023-12-01', '2024-04-28', '2024-06-04');


SELECT 
    DATE(MTM.START_TIME) AS TRIP_DATE,
    SUM(MTM.TOTAL_PASSENGERS) AS TOTAL_PASSENGERS,
    COUNT(*) AS NO_OF_TRIPS,
    UC.DAY,
    UC.IS_HOLIDAY,
    ec.is_event
FROM
    RAW_DATA.MST_TRANSACTION_MASTER AS MTM
FULL JOIN 
    RAW_SOURCE_DATA.UP_CALENDAR AS UC
ON
    DATE(MTM.START_TIME) = UC.DATE
LEFT JOIN 
    raw_source_data.hardoi_event_calendar AS ec
ON
    DATE(MTM.START_TIME) = ec.date
WHERE
    (MTM.ROUTE_ID = 910)
    AND
        MTM.time_valid = TRUE
GROUP BY 
    DATE(MTM.START_TIME), UC.DAY, UC.IS_HOLIDAY, ec.is_event
ORDER BY
    TRIP_DATE;


select distinct(route_id) from raw_data.mst_transaction_master;

select count(*) from raw_data.mst_transaction_master where route_id = 180;