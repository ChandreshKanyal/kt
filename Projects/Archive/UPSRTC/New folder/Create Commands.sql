-- Create Commands 

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

--Weather 

CREATE TABLE weather_data (
    datetime DATE,
    temp FLOAT,
    feelslike FLOAT,
    humidity FLOAT,
    precip FLOAT,
    preciptype VARCHAR(20),
    windspeed FLOAT,
    visibility FLOAT,
    severerisk INT,
    conditions VARCHAR(50)
);

select * from raw_source_data.weather;