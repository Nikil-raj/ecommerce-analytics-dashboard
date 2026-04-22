import snowflake.connector

def get_connection():
    conn = snowflake.connector.connect(
        user="Nikil",
        password="Nikilrajsandy@0509",
        account="DBJCKMW-OA63272",
        warehouse="Compute_WH",
        database="DATA_ANALYTICS",
        schema="RAW_DATA"
    )
    return conn