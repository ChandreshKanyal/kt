from utils.redshift import get_redshift_conn

def run_procedure():
    conn = get_redshift_conn()
    conn.autocommit = True  # REQUIRED for Redshift procedures
    cur = conn.cursor()

    cur.execute("CALL merge_transaction_master_1();")

    cur.close()
    conn.close()

if __name__ == "__main__":
    run_procedure()
