import pandas as pd
from utils.snowflake_conn import get_connection
import streamlit as st

@st.cache_data
def run_query(query):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(query)
    df = pd.DataFrame(cur.fetchall(), columns=[col[0] for col in cur.description])
    cur.close()
    conn.close()
    return df