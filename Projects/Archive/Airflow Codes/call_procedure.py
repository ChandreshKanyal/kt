from airflow import DAG
from airflow.providers.postgres.operators.postgres import PostgresOperator
from pendulum import datetime

default_args = {
    'owner': 'airflow',
    'retries': 1,
}

with DAG(
    dag_id='run_redshift_procedure',
    default_args=default_args,
    schedule_interval=None,  # run manually
    start_date=datetime(2024, 7, 1),
    catchup=False,
    tags=['transit'],
) as dag:

    call_stored_procedure = PostgresOperator(
        task_id='call_merge_transaction_master',
        postgres_conn_id='redshift_conn',  # Replace with your actual Redshift connection ID
        sql="CALL merge_transaction_master_1();",
    )

    call_stored_procedure
