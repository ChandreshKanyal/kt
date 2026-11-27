from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.providers.postgres.operators.postgres import PostgresOperator
from datetime import datetime
import boto3
from airflow.providers.postgres.hooks.postgres import PostgresHook
from airflow.providers.amazon.aws.hooks.s3 import S3Hook
from pendulum import datetime
import pandas as pd

# Config
REGION = 'ap-south-1'
EC2_INSTANCE_ID = 'i-0c85d46c3bfce8d5c'
REDSHIFT_CLUSTER_ID = 'transit-da-cluster'
SAGEMAKER_NOTEBOOK_NAME = 'transit-db-notebook'

TABLE_NAME = 'snapshot_1.bus_route'
REDSHIFT_TABLE = 'raw_source_data.bus_route'
LOCAL_FILE = f'/tmp/{TABLE_NAME}.csv'
S3_BUCKET = 'test-airflow-chan'
S3_KEY = f'data/{TABLE_NAME}.csv'
IAM_ROLE = 'arn:aws:iam::590184098502:role/service-role/AmazonRedshift-CommandsAccessRole-20240718T135548'

# EC2
def check_and_start_ec2():
    ec2 = boto3.client('ec2', region_name=REGION)
    response = ec2.describe_instances(InstanceIds=[EC2_INSTANCE_ID])
    state = response['Reservations'][0]['Instances'][0]['State']['Name']

    if state == 'running':
        print(f"EC2 instance {EC2_INSTANCE_ID} is already running.")
    else:
        print(f"Starting EC2 instance {EC2_INSTANCE_ID}...")
        ec2.start_instances(InstanceIds=[EC2_INSTANCE_ID])
        print("Waiting for EC2 instance to be in running state...")
        waiter = ec2.get_waiter('instance_running')
        waiter.wait(InstanceIds=[EC2_INSTANCE_ID])
        print(f"EC2 instance {EC2_INSTANCE_ID} is now running.")

# Redshift
def check_and_start_redshift():
    redshift = boto3.client('redshift', region_name=REGION)
    response = redshift.describe_clusters(ClusterIdentifier=REDSHIFT_CLUSTER_ID)
    status = response['Clusters'][0]['ClusterStatus']

    if status == 'available':
        print(f"Redshift cluster '{REDSHIFT_CLUSTER_ID}' is already available.")
    else:
        print(f"Starting Redshift cluster '{REDSHIFT_CLUSTER_ID}'...")
        redshift.resume_cluster(ClusterIdentifier=REDSHIFT_CLUSTER_ID)
        print("Waiting for Redshift cluster to be available...")
        waiter = redshift.get_waiter('cluster_available')
        waiter.wait(ClusterIdentifier=REDSHIFT_CLUSTER_ID)
        print(f"Redshift cluster '{REDSHIFT_CLUSTER_ID}' is now available.")

# SageMaker
def check_and_start_sagemaker():
    sagemaker = boto3.client('sagemaker', region_name=REGION)
    response = sagemaker.describe_notebook_instance(NotebookInstanceName=SAGEMAKER_NOTEBOOK_NAME)
    status = response['NotebookInstanceStatus']

    if status == 'InService':
        print(f"SageMaker notebook '{SAGEMAKER_NOTEBOOK_NAME}' is already ON.")
    else:
        print(f"Starting SageMaker notebook '{SAGEMAKER_NOTEBOOK_NAME}'...")
        sagemaker.start_notebook_instance(NotebookInstanceName=SAGEMAKER_NOTEBOOK_NAME)
        print("Waiting for notebook to be InService...")
        waiter = sagemaker.get_waiter('notebook_instance_in_service')
        waiter.wait(
            NotebookInstanceName=SAGEMAKER_NOTEBOOK_NAME,
            WaiterConfig={'Delay': 30, 'MaxAttempts': 20}
        )
        print(f"SageMaker notebook '{SAGEMAKER_NOTEBOOK_NAME}' is now ON.")

# Final Step
def all_services_ready():
    print("All services (EC2, Redshift, SageMaker) are ready.")

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

call_stored_procedure = PostgresOperator(
        task_id='call_merge_transaction_master',
        postgres_conn_id='redshift_conn',  # Replace with your actual Redshift connection ID
        sql="CALL merge_transaction_master_1();",
    )

default_args = {
    'owner': 'airflow',
    'start_date': datetime(2023, 1, 1),
    'retries': 1,
}

with DAG(
    dag_id='full_dag_trial',
    default_args=default_args,
    schedule=None,
    catchup=False,
    tags= ['transit']
) as dag:

    ec2_task = PythonOperator(
        task_id='check_and_start_ec2',
        python_callable=check_and_start_ec2
    )

    redshift_task = PythonOperator(
        task_id='check_and_start_redshift',
        python_callable=check_and_start_redshift
    )

    sagemaker_task = PythonOperator(
        task_id='check_and_start_sagemaker',
        python_callable=check_and_start_sagemaker
    )

    final_task = PythonOperator(
        task_id='all_services_ready',
        python_callable=all_services_ready
    )

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

    [ec2_task, redshift_task, sagemaker_task] >> final_task >> extract_data >> upload_s3 >> load_redshift >>  call_stored_procedure
