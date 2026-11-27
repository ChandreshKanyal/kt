from utils.redshift import get_redshift_conn

def run_procedure():
    conn = get_redshift_conn()
    conn.autocommit = True
    cur = conn.cursor()

    unload_sql = """
    UNLOAD ('
        SELECT *
        FROM raw_data.mst_transaction_master_1
        WHERE dwh_crddt >
        (
            SELECT end_time
            FROM raw_data.data_ingestion_tracking_1
            ORDER BY end_time DESC
            OFFSET 1
            LIMIT 1
        )
    ')
    TO 's3://test-airflow-chan/incremental_data/incre_1_'
    IAM_ROLE 'arn:aws:iam::590184098502:role/service-role/AmazonRedshift-CommandsAccessRole-20240718T135548'
    FORMAT AS CSV
    HEADER
    ALLOWOVERWRITE;
    """

    cur.execute(unload_sql)

    cur.close()
    conn.close()

if __name__ == "__main__":
    run_procedure()
