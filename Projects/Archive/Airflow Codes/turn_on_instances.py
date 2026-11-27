from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime
import boto3

# Config
REGION = 'ap-south-1'
EC2_INSTANCE_ID = 'i-0c85d46c3bfce8d5c'
REDSHIFT_CLUSTER_ID = 'transit-da-cluster'
SAGEMAKER_NOTEBOOK_NAME = 'transit-db-notebook'

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

default_args = {
    'owner': 'airflow',
    'start_date': datetime(2023, 1, 1),
    'retries': 1,
}

with DAG(
    dag_id='start_all_aws_services',
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

    [ec2_task, redshift_task, sagemaker_task] >> final_task
