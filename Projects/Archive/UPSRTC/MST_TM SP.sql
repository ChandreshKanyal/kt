CREATE OR REPLACE PROCEDURE merge_transaction_master_1()
AS $$
DECLARE
  v_error_message TEXT;
  v_error_code TEXT;
  last_run TIMESTAMP; -- Tracks the last processed timestamp
  v_row_count INT;
  v_row_count_scd2 INT;
  v_start_time TIMESTAMP := CURRENT_TIMESTAMP;
  v_end_time TIMESTAMP;
  v_success BOOLEAN := TRUE;

BEGIN
  -- Step 1: Calculate the last processed date
  BEGIN
        last_run := (SELECT COALESCE(MAX(start_time), '2024-12-01')
                    FROM raw_data.data_ingestion_tracking_1);
  EXCEPTION
    WHEN OTHERS THEN
      v_error_message := SQLERRM;
      v_error_code := SQLSTATE;
      v_success := FALSE;
      INSERT INTO raw_data.error_log_1 (
         procedure_name, error_message, error_code, rec_date
      ) VALUES (
         'merge_transaction_master_1 - Step 1', v_error_message, v_error_code, CURRENT_TIMESTAMP
      );
      RETURN;
  END;

  -- Proceed only if Step 1 was successful
  IF v_success THEN
       -- Step 2.1: Create temp_afc_transaction_details
    BEGIN
      DROP TABLE IF EXISTS temp_afc_transaction_details;
      CREATE TEMP TABLE temp_afc_transaction_details AS
      SELECT
          TATD.schedule_id AS trip_id,
          MIN(TATD.issue_date) AS trip_start_time,
          MAX(TATD.issue_date) AS trip_end_time,
		      SUM(TATD.transaction_amount) AS total_income,
		      SUM(no_of_passengers) AS total_passengers,
          TATD.region_code AS region_id,
          MIN(TATD.integration_date)	  
          FROM raw_data.AFC_TRANSACTION_DETAILS TATD 
      --WHERE trip_start_time > last_run
      --WHERE TATD.integration_date > last_run 
	        WHERE TATD.expence_id is NULL
	        AND TATD.cancel_type != 'Canceled'
          GROUP BY TATD.schedule_id, TATD.region_code
          having trip_start_time > last_run;
	  
    EXCEPTION
      WHEN OTHERS THEN
        v_error_message := SQLERRM;
        v_error_code := SQLSTATE;
        v_success := FALSE;
        INSERT INTO raw_data.error_log_1 (
           procedure_name, error_message, error_code, rec_date
        ) VALUES (
           'merge_transaction_master_1 - Step 2.1', v_error_message, v_error_code, CURRENT_TIMESTAMP
        );
        RETURN;
    END;

    -- Step 2.2: Create temp_bus_trip_schedule
    BEGIN
      DROP TABLE IF EXISTS temp_bus_trip_schedule;
      CREATE TEMP TABLE temp_bus_trip_schedule AS
      SELECT
          TBTS.id,
          TBTS.status,
		  TBTS.bus_schedule_instance,
          TBTS.bus_route_id,
          TBTS.last_edit_date
      FROM raw_data.BUS_TRIP_SCHEDULE TBTS
      WHERE TBTS.status = 'OK' AND TBTS.create_date > last_run;
    EXCEPTION
      WHEN OTHERS THEN
        v_error_message := SQLERRM;
        v_error_code := SQLSTATE;
        v_success := FALSE;
        INSERT INTO raw_data.error_log_1 (
           procedure_name, error_message, error_code, rec_date
        ) VALUES (
           'merge_transaction_master_1 - Step 2.3', v_error_message, v_error_code, CURRENT_TIMESTAMP
        );
        RETURN;
    END;

    -- Step 2.3: Create temp_bus_schedule_setting_instance
    BEGIN
      DROP TABLE IF EXISTS temp_bus_schedule_setting_instance;
      CREATE TEMP TABLE temp_bus_schedule_setting_instance AS
      SELECT
          TBSSI.waybill_number,
          TBSSI.id,
          TBSSI.etim_device_id,
          TBSSI.conductor_id,
          TBSSI.driver_id,
          TBSSI.support_driver_id,
          TBSSI.duty_type,
          TBSSI.bus_id,
          TBSSI.end_date,
		  TBSSI.create_date
      FROM raw_data.BUS_SCHEDULE_SETTING_INSTANCE TBSSI
      WHERE TBSSI.create_date > last_run;
	  
    EXCEPTION
      WHEN OTHERS THEN
        v_error_message := SQLERRM;
        v_error_code := SQLSTATE;
        v_success := FALSE;
        INSERT INTO raw_data.error_log_1 (
           procedure_name, error_message, error_code, rec_date
        ) VALUES (
           'merge_transaction_master_1 - Step 2.4', v_error_message, v_error_code, CURRENT_TIMESTAMP
        );
        RETURN;
    END;

    -- Step 2.4: Create temp_bus
    BEGIN
      DROP TABLE IF EXISTS temp_bus;
      CREATE TEMP TABLE temp_bus AS
      SELECT
          TBUS.plate AS bus_number_plate,
          TBUS.id AS vehicle_id,
          TBUS.last_edit_date
      FROM raw_data.BUS TBUS;
     -- WHERE TBUS.last_edit_date > last_run;
    EXCEPTION
      WHEN OTHERS THEN
        v_error_message := SQLERRM;
        v_error_code := SQLSTATE;
        v_success := FALSE;
        INSERT INTO raw_data.error_log_1 (
           procedure_name, error_message, error_code, rec_date
        ) VALUES (
           'merge_transaction_master_1 - Step 2.5', v_error_message, v_error_code, CURRENT_TIMESTAMP
        );
        RETURN;
    END;

    -- Step 2.5: Create temp_bus_region
    BEGIN
      DROP TABLE IF EXISTS temp_bus_region;
      CREATE TEMP TABLE temp_bus_region AS
      SELECT
	      TBR.code as region_id,
          TBR.name AS region_name,
          TBR.create_date
      FROM raw_data.BUS_REGION TBR;
      --WHERE TBR.create_date > last_run;
    EXCEPTION
      WHEN OTHERS THEN
        v_error_message := SQLERRM;
        v_error_code := SQLSTATE;
        v_success := FALSE;
        INSERT INTO raw_data.error_log_1 (
           procedure_name, error_message, error_code, rec_date
        ) VALUES (
           'merge_transaction_master_1 - Step 2.6', v_error_message, v_error_code, CURRENT_TIMESTAMP
        );
        RETURN;
    END;

    -- Step 2.6: Create temp_bus_route
    BEGIN
      DROP TABLE IF EXISTS temp_bus_route;
      CREATE TEMP TABLE temp_bus_route AS
      SELECT DISTINCT
          TBS.route_id,
          TBS.route_name,
          TBS.create_date
      FROM raw_data.mst_route_master TBS;
   --   WHERE TBS.create_date > last_run;
    EXCEPTION
      WHEN OTHERS THEN
        v_error_message := SQLERRM;
        v_error_code := SQLSTATE;
        v_success := FALSE;
        INSERT INTO raw_data.error_log_1 (
           procedure_name, error_message, error_code, rec_date
        ) VALUES (
           'merge_transaction_master_1 - Step 2.7', v_error_message, v_error_code, CURRENT_TIMESTAMP
        );
        RETURN;
    END;
  END IF;

  IF v_success THEN
    -- Step 3: Combine these temporary tables
    BEGIN
      DROP TABLE IF EXISTS temp_combined_data;
      CREATE TEMP TABLE temp_combined_data AS
      SELECT
          TATD.region_id,
          TBR.region_name,
          TBTS.bus_route_id,
          TBS.route_name,
          TATD.trip_id,
          TATD.trip_start_time AS start_time,
          TATD.trip_end_time AS end_time,
          TATD.total_income,
          TATD.total_passengers,
          TBTS.status AS trip_status,
          TBSSI.waybill_number,
          TBSSI.conductor_id,
          TBSSI.driver_id,
          TBSSI.support_driver_id,
          TBSSI.id AS schedule_id,
          TBSSI.etim_device_id,
          TBSSI.duty_type,
          TBSSI.bus_id,
          TBUS.bus_number_plate
      FROM temp_afc_transaction_details TATD
      INNER JOIN temp_bus_trip_schedule TBTS ON TBTS.id = TATD.trip_id
      INNER JOIN temp_bus_schedule_setting_instance TBSSI ON TBSSI.id = TBTS.bus_schedule_instance
      INNER JOIN temp_bus TBUS ON TBUS.vehicle_id = TBSSI.bus_id
      INNER JOIN temp_bus_route TBS ON TBS.route_id = TBTS.bus_route_id
      INNER JOIN temp_bus_region TBR ON TBR.region_id = TATD.region_id;
    EXCEPTION
      WHEN OTHERS THEN
        v_error_message := SQLERRM;
        v_error_code := SQLSTATE;
        v_success := FALSE;
        INSERT INTO raw_data.error_log_1 (
           procedure_name, error_message, error_code, rec_date
        ) VALUES (
           'merge_transaction_master_1 - Step 3', v_error_message, v_error_code, CURRENT_TIMESTAMP
        );
        RETURN;
    END;
  END IF;

  IF v_success THEN
    -- Step 4: SCD2 Update Logic
    BEGIN
      UPDATE raw_data.mst_transaction_master_1
      SET DWH_UPDDT = CURRENT_TIMESTAMP, DWH_ACTIVE = FALSE
      FROM temp_combined_data
      WHERE mst_transaction_master_1.trip_id = temp_combined_data.trip_id
      AND mst_transaction_master_1.DWH_ACTIVE = TRUE;

      GET DIAGNOSTICS v_row_count_scd2 = ROW_COUNT;
      RAISE INFO ' % existing rows updated.', v_row_count_scd2;

    EXCEPTION
      WHEN OTHERS THEN
        v_error_message := SQLERRM;
        v_error_code := SQLSTATE;
        v_success := FALSE;
        ROLLBACK;
        INSERT INTO raw_data.error_log_1 (
           procedure_name, error_message, error_code, rec_date
        ) VALUES (
           'merge_transaction_master_1 - Step 4', v_error_message, v_error_code, CURRENT_TIMESTAMP
        );
        RETURN;
    END;
  END IF;

  IF v_success THEN
    -- Step 5: Insert new records with 'time_valid' flag
    BEGIN
      INSERT INTO raw_data.mst_transaction_master_1 (
          region_id, region_name, route_id, route_name, waybill_number, trip_id, start_time, end_time, 
          total_income, total_passengers, trip_status, conductor_id, driver_id, support_driver_id, 
          schedule_id, etim_device_id, duty_type, bus_id, bus_number_plate, 
          time_valid
      )
     SELECT
    region_id, region_name, bus_route_id, route_name, waybill_number, trip_id, start_time, end_time, total_income, 
    total_passengers, trip_status, conductor_id, driver_id, support_driver_id, schedule_id, etim_device_id, duty_type, bus_id, 
    bus_number_plate,
    CASE 
        WHEN start_time > end_time THEN FALSE 
        WHEN EXTRACT(YEAR FROM start_time) > 2026 OR EXTRACT(YEAR FROM end_time) > 2026 THEN FALSE
        ELSE TRUE 
    END AS time_valid
    FROM temp_combined_data;

      GET DIAGNOSTICS v_row_count = ROW_COUNT;

    EXCEPTION
      WHEN OTHERS THEN
        v_error_message := SQLERRM;
        v_error_code := SQLSTATE;
        v_success := FALSE;
        INSERT INTO raw_data.error_log_1 (
           procedure_name, error_message, error_code, rec_date
        ) VALUES (
           'merge_transaction_master - Step 5', v_error_message, v_error_code, CURRENT_TIMESTAMP
        );
        RETURN;
    END;
  END IF;

  IF v_success THEN
    -- Step 6: Update tracking
    BEGIN
      v_end_time := CURRENT_TIMESTAMP;
      INSERT INTO raw_data.data_ingestion_tracking_1 (
          table_name, row_count, start_time, end_time
      ) VALUES (
          'mst_transaction_master_1', v_row_count, v_start_time, v_end_time
      );
    EXCEPTION
      WHEN OTHERS THEN
        v_error_message := SQLERRM;
        v_error_code := SQLSTATE;
        INSERT INTO raw_data.error_log (
           procedure_name, error_message, error_code, rec_date
        ) VALUES (
           'merge_transaction_master_1 - Step 6', v_error_message, v_error_code, CURRENT_TIMESTAMP
        );
    END;
  END IF;

  RAISE INFO 'Merge Transaction Master completed successfully with % rows inserted.', v_row_count;

END;
$$ LANGUAGE plpgsql;

-- Call the procedure to execute it
CALL merge_transaction_master_1();