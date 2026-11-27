from airflow import DAG
from airflow.providers.postgres.hooks.postgres import PostgresHook
from airflow.providers.amazon.aws.hooks.s3 import S3Hook
from airflow.operators.python import PythonOperator
from pendulum import datetime
import pandas as pd
import os

# Table configuration: {Postgres: Redshift}
TABLES = {
    'afc_transaction_details': 'demo.afc_transaction_details_demo',
    'bus': 'demo.bus_demo',
    'bus_region': 'demo.bus_region_demo',
    'bus_schedule_setting_instance': 'demo.bus_schedule_setting_instance_demo',
    'bus_trip_schedule': 'demo.bus_trip_schedule_demo'
}

S3_BUCKET = 'test-airflow-chan'
IAM_ROLE = 'arn:aws:iam::590184098502:role/service-role/AmazonRedshift-CommandsAccessRole-20240718T135548'

default_args = {
    'owner': 'airflow',
    'retries': 1,
}

def extract_data_to_csv(table, local_file):
    def _extract(**kwargs):
        pg_hook = PostgresHook(postgres_conn_id='postgres_ec2')
        df = pg_hook.get_pandas_df(f"SELECT * FROM snapshot_1.{table}")
        df.to_csv(local_file, index=False)
    return _extract

def upload_to_s3(local_file, s3_key):
    def _upload(**kwargs):
        s3 = S3Hook(aws_conn_id='aws_default')
        s3.load_file(
            filename=local_file,
            key=s3_key,
            bucket_name=S3_BUCKET,
            replace=True
        )
    return _upload

def copy_to_redshift(redshift_table, s3_key):
    def _copy(**kwargs):
        rs_hook = PostgresHook(postgres_conn_id='redshift_conn')
        copy_sql = f"""
            COPY {redshift_table}
            FROM 's3://{S3_BUCKET}/{s3_key}'
            IAM_ROLE '{IAM_ROLE}'
            FORMAT AS CSV
            IGNOREHEADER 1;
        """
        rs_hook.run(copy_sql)
    return _copy

with DAG(
    dag_id='etl_multi_table',
    default_args=default_args,
    schedule=None,
    start_date=datetime(2024, 7, 1),
    catchup=False,
    tags=['transit']
) as dag:

    for table, redshift_table in TABLES.items():
        table_clean_name = table.replace('.', '_')
        local_file = f'/tmp/{table_clean_name}.csv'
        s3_key = f'data/{table_clean_name}.csv'

        extract_task = PythonOperator(
            task_id=f'extract_{table_clean_name}',
            python_callable=extract_data_to_csv(table, local_file)
        )

        upload_task = PythonOperator(
            task_id=f'upload_{table_clean_name}_to_s3',
            python_callable=upload_to_s3(local_file, s3_key)
        )

        load_task = PythonOperator(
            task_id=f'copy_{table_clean_name}_to_redshift',
            python_callable=copy_to_redshift(redshift_table, s3_key)
        )

        extract_task >> upload_task >> load_task
