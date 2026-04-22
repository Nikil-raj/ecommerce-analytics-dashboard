import os
from dotenv import load_dotenv
import google.generativeai as genai

# Load environment variables
load_dotenv()

# Configure Gemini API
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

# Initialize model
model = genai.GenerativeModel("gemini-1.5-flash")


def clean_sql(text):
    """
    Cleans SQL output from Gemini (removes ```sql blocks)
    """
    return text.replace("```sql", "").replace("```", "").strip()


def generate_sql(question):
    """
    Convert natural language question to SQL query
    """

    prompt = f"""
    You are a data analyst working with an e-commerce database.

    Tables:
    - customers(customer_id, customer_unique_id, customer_state)
    - orders(order_id, customer_id, order_purchase_timestamp)
    - order_items(order_id, product_id, price)

    Rules:
    - Use proper SQL syntax compatible with Snowflake
    - Always use JOIN when needed
    - Use DATE_TRUNC('month', ...) for monthly data
    - Return ONLY SQL query (no explanation)

    Question: {question}
    """

    response = model.generate_content(prompt)

    return clean_sql(response.text)