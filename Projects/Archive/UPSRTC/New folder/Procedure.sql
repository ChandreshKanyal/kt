--MST ROUTE MASTER PEOCEDURE CODE

-- Step 1: Create the Master Table
CREATE TABLE IF NOT EXISTS raw_data.MST_ROUTE_MASTER (
  DWH_RID BIGINT IDENTITY(1,1) PRIMARY KEY,
  DWH_CRDDT TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  DWH_UPDDT TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  DWH_ACTIVE BOOLEAN DEFAULT TRUE,
  DWH_UPDDBY VARCHAR(50) DEFAULT current_user,
  ROUTE_ID BIGINT,
  ROUTE_NAME VARCHAR,
  ROUTE_TYPE VARCHAR,
  CREATE_DATE TIMESTAMP,
  DELETED BOOLEAN,
  SOURCE_STOP_ID BIGINT,               
  DESTINATION_STOP_ID BIGINT,          
  SOURCE_NAME VARCHAR,                  
  DESTINATION_NAME VARCHAR,             
  ROUTE_LENGTH FLOAT,                                     
  ROUTE_STOP_ID BIGINT,                
  ROUTE_STOP_NAME VARCHAR,            
  ROUTE_STOP_ORDER INT,    
  STOP_DIST_FRM_SRC INT,             
  STOP_PINCODE VARCHAR            
);

-- Step 2: Create the Error Log Table
CREATE TABLE IF NOT EXISTS raw_data.error_log (
   id BIGINT IDENTITY(1,1) PRIMARY KEY,
   procedure_name VARCHAR,
   error_message TEXT,
   error_code VARCHAR(10),
   rec_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Step 3: Create the Data Ingestion Tracking Table
CREATE TABLE IF NOT EXISTS raw_data.data_ingestion_tracking (
   id BIGINT IDENTITY(1,1) PRIMARY KEY,
   table_name VARCHAR,
 --last_processed TIMESTAMP,
   row_count INT,
   start_time TIMESTAMP,
   end_time TIMESTAMP
 --rec_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);


-- Step 4: Procedure to merge data into the master table
  CREATE OR REPLACE PROCEDURE merge_route_master()
  AS $$ 
  DECLARE
    v_error_message TEXT;
    v_error_code TEXT;
    last_run TIMESTAMP; 
    v_row_count INT;
    v_row_count_scd2 INT;
    v_start_time TIMESTAMP := CURRENT_TIMESTAMP;
    v_end_time TIMESTAMP;
    v_success BOOLEAN := TRUE;

  BEGIN
    -- Begin transaction block
    BEGIN
      -- Step 1: Calculate the last processed date
      BEGIN
        last_run := (SELECT COALESCE(MAX(start_time), '1970-01-01')
                    FROM raw_data.data_ingestion_tracking
                    WHERE table_name = 'MST_ROUTE_MASTER');
      EXCEPTION
        WHEN OTHERS THEN
          v_error_message := SQLERRM;
          v_error_code := SQLSTATE;
          v_success := FALSE;
          -- Log error
          INSERT INTO raw_data.error_log (
            procedure_name, error_message, error_code, rec_date
          ) VALUES (
            'merge_route_master - Last Processed Date', v_error_message, v_error_code, CURRENT_TIMESTAMP
          );
          RETURN;
      END;

      -- Step 2: Create temporary table for staging data
      IF v_success THEN
        BEGIN
          DROP TABLE IF EXISTS temp_route_data;
          CREATE TEMP TABLE temp_route_data AS
          SELECT 
              r_filtered.id AS ROUTE_ID, 
              r_filtered.name AS ROUTE_NAME, 
              r_filtered.route_type AS ROUTE_TYPE,
              r_filtered.create_date AS CREATE_DATE,
              ri.DELETED,
              ri.SOURCE_STOP_ID,
              ri.SOURCE_NAME,
              ri.DESTINATION_STOP_ID,
              ri.DESTINATION_NAME,
              rl.max_distance AS ROUTE_LENGTH,
              rs.ROUTE_STOP_ID,
              rs.ROUTE_STOP_NAME,
              rs.ROUTE_STOP_ORDER,
              rs.STOP_DIST_FRM_SRC,                          
              rs.STOP_PINCODE                     
          FROM 
              (SELECT * 
              FROM raw_data.bus_route r
              WHERE r.create_date > last_run
              OR r.last_edit_date > last_run) r_filtered
          LEFT JOIN 
              raw_source_data.vw_max_route_length rl ON r_filtered.id = rl.bus_route_id
          LEFT JOIN 
              raw_source_data.vw_route_info ri ON r_filtered.id = ri.ROUTE_ID
          LEFT JOIN 
              raw_source_data.vw_route_stops rs ON r_filtered.id = rs.ROUTE_ID;

        EXCEPTION
          WHEN OTHERS THEN
            v_error_message := SQLERRM;
            v_error_code := SQLSTATE;
            v_success := FALSE;
            -- Log error
            INSERT INTO raw_data.error_log (
              procedure_name, error_message, error_code, rec_date
            ) VALUES (
              'merge_route_master - Create Temp Table', v_error_message, v_error_code, CURRENT_TIMESTAMP
            );
            
            RETURN;
        END;
      END IF;

      -- Step 3: SCD2 Update Logic for existing records
      IF v_success THEN
        BEGIN
          -- Mark old records as inactive
          UPDATE raw_data.MST_ROUTE_MASTER
          SET DWH_UPDDT = CURRENT_TIMESTAMP, DWH_ACTIVE = FALSE
          FROM temp_route_data
          WHERE MST_ROUTE_MASTER.ROUTE_ID = temp_route_data.ROUTE_ID AND 
                MST_ROUTE_MASTER.ROUTE_STOP_ID = temp_route_data.ROUTE_STOP_ID;

          GET DIAGNOSTICS v_row_count_scd2 = ROW_COUNT;
          RAISE INFO ' % existing rows updated.', v_row_count_scd2;

        EXCEPTION
          WHEN OTHERS THEN
            v_error_message := SQLERRM;
            v_error_code := SQLSTATE;
            v_success := FALSE;
            -- Log error
        -- ROLLBACK on failure
            ROLLBACK;
            INSERT INTO raw_data.error_log (
              procedure_name, error_message, error_code, rec_date
            ) VALUES (
              'merge_route_master - Update Logic', v_error_message, v_error_code, CURRENT_TIMESTAMP
            );
            
            RETURN;
        END;
      END IF;
    
      IF v_success THEN
        BEGIN
          -- Insert new records
          INSERT INTO raw_data.MST_ROUTE_MASTER (
              ROUTE_ID, ROUTE_NAME, ROUTE_TYPE, CREATE_DATE, DELETED,
              SOURCE_STOP_ID, SOURCE_NAME, DESTINATION_STOP_ID, DESTINATION_NAME, 
              ROUTE_LENGTH, ROUTE_STOP_ID, ROUTE_STOP_NAME, ROUTE_STOP_ORDER,
              STOP_DIST_FRM_SRC, STOP_PINCODE)
          SELECT
              temp_route_data.ROUTE_ID, temp_route_data.ROUTE_NAME, temp_route_data.ROUTE_TYPE, temp_route_data.CREATE_DATE, temp_route_data.DELETED,
              temp_route_data.SOURCE_STOP_ID, temp_route_data.SOURCE_NAME, temp_route_data.DESTINATION_STOP_ID, temp_route_data.DESTINATION_NAME,
              temp_route_data.ROUTE_LENGTH, temp_route_data.ROUTE_STOP_ID, temp_route_data.ROUTE_STOP_NAME, temp_route_data.ROUTE_STOP_ORDER,
              temp_route_data.STOP_DIST_FRM_SRC, temp_route_data.STOP_PINCODE
          FROM
              temp_route_data;
          --v_row_count := (SELECT COUNT(*) FROM temp_route_data);
      GET DIAGNOSTICS v_row_count = ROW_COUNT;
      

        EXCEPTION
          WHEN OTHERS THEN
            v_error_message := SQLERRM;
            v_error_code := SQLSTATE;
            v_success := FALSE;
        -- ROLLBACK on failure
            ROLLBACK;
        -- Log error
            INSERT INTO raw_data.error_log (
              procedure_name, error_message, error_code, rec_date
            ) VALUES (
              'merge_route_master - Insert New Records', v_error_message, v_error_code
            );
            
            RETURN;
        END;
      END IF;

      -- Step 4: Update tracking table
      IF v_success THEN
        BEGIN
          v_end_time := CURRENT_TIMESTAMP;
          INSERT INTO raw_data.data_ingestion_tracking (
            table_name, row_count, start_time, end_time
          ) VALUES (
            'MST_ROUTE_MASTER', v_row_count, v_start_time, v_end_time
          );
        EXCEPTION
          WHEN OTHERS THEN
            v_error_message := SQLERRM;
            v_error_code := SQLSTATE;
            -- Log error without rollback, as tracking does not affect the data integrity
            INSERT INTO raw_data.error_log (
              procedure_name, error_message, error_code, rec_date
            ) VALUES (
              'merge_route_master - Update Tracking Table', v_error_message, v_error_code, CURRENT_TIMESTAMP
            );
        END;
      END IF;

      -- Commit the transaction if everything is successful
      IF v_success THEN
        COMMIT;
      END IF;

    EXCEPTION
      -- Final error handling to rollback the transaction
      WHEN OTHERS THEN
        ROLLBACK;
        RAISE INFO 'Transaction rolled back due to error: %', SQLERRM;
    END;

    RAISE INFO 'Merge Route Master completed successfully with % rows inserted.', v_row_count;
  END; 
  $$ LANGUAGE plpgsql;
  -- Call the procedure to execute it
  CALL merge_route_master();