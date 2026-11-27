from airflow import DAG
from airflow.providers.postgres.hooks.postgres import PostgresHook
from airflow.providers.amazon.aws.hooks.s3 import S3Hook
from airflow.operators.python import PythonOperator
from pendulum import datetime
import pandas as pd

# Configurable Constants
TABLE_NAME = 'snapshot_1.bus_route'
REDSHIFT_TABLE = 'raw_source_data.bus_route'
LOCAL_FILE = f'/tmp/{TABLE_NAME}.csv'
S3_BUCKET = 'test-airflow-chan'
S3_KEY = f'data/{TABLE_NAME}.csv'
IAM_ROLE = 'arn:aws:iam::590184098502:role/service-role/AmazonRedshift-CommandsAccessRole-20240718T135548'

default_args = {
    'owner': 'airflow',
    'retries': 1,
}

with DAG(
    dag_id='load_existing_table_to_redshift',
    default_args=default_args,
    schedule=None,
    start_date=datetime(2024, 7, 1),
    catchup=False,
    tags=['transit']
) as dag:

    def extract_data_to_csv(**kwargs):
        pg_hook = PostgresHook(postgres_conn_id='postgres_ec2')
        df = pg_hook.get_pandas_df(f"SELECT * FROM {TABLE_NAME}")
        df.to_csv(LOCAL_FILE, index=False)

    def upload_to_s3(**kwargs):
        s3 = S3Hook(aws_conn_id='aws_default')
        s3.load_file(
            filename=LOCAL_FILE,
            key=S3_KEY,
            bucket_name=S3_BUCKET,
            replace=True
        )

    def copy_to_redshift(**kwargs):
        rs_hook = PostgresHook(postgres_conn_id='redshift_conn')
        copy_sql = f"""
            COPY {REDSHIFT_TABLE}
            FROM 's3://{S3_BUCKET}/{S3_KEY}'
            IAM_ROLE '{IAM_ROLE}'
            FORMAT AS CSV
            IGNOREHEADER 1;
            """
        rs_hook.run(copy_sql)
        
    extract_data = PythonOperator(
        task_id='extract_data_to_csv',
        python_callable=extract_data_to_csv
    )

    upload_s3 = PythonOperator(
        task_id='upload_to_s3',
        python_callable=upload_to_s3
    )

    load_redshift = PythonOperator(
        task_id='copy_to_redshift',
        python_callable=copy_to_redshift
    )

    extract_data >> upload_s3 >> load_redshift