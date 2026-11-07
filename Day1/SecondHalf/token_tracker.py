import sqlite3
from datetime import datetime,date
import tiktoken
from SecondHalf.config import(
    MODEL_PRICES,
    MAX_CONTEXT_TOKENS
)
DATABASE="usage.db"
def count_tokens(messages,model):
    try:
        encoding=tiktoken.encoding_for_model(model)
    except KeyError:
        encoding=tiktoken.get_encoding("cl100k_base")
    total_tokens=0
    for message in messages:
        role=message.get("role","")
        content=message.get("content","")
        total_tokens+=len(encoding.encode(role))
        total_tokens+=len(encoding.encode(str(content)))
        total_tokens+=4
    return total_tokens
def check_context_limit(messages,model):
    estimated_tokens=count_tokens(messages,model)
    if estimated_tokens>MAX_CONTEXT_TOKENS:
        raise ValueError("Request exceeds the context token limit")
    return estimated_tokens

def calculate_cost(
        prompt_tokens,
        completion_tokens,
        model
):
    prices=MODEL_PRICES.get(model)
    if prices is None:
        raise ValueError("Model pricing not configured")
    input_cost=(prompt_tokens*prices["input"]/1_000_000)
    output_cost=(completion_tokens*prices["output"]/1_000_000)
    total_cost=input_cost+output_cost
    return total_cost
def create_database():
    connection=sqlite3.connect(DATABASE)
    cursor=connection.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS usage_logs(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT,
            model TEXT,
            prompt_tokens INTEGER,
            completion_tokens INTEGER,
            total_tokens INTEGER,
            cost REAL
            )
        """)
    connection.commit()
    connection.close()
def save_usage(
        model,
        prompt_tokens,
        completion_tokens,
        cost
):
    connection=sqlite3.connect(DATABASE)
    cursor=connection.cursor()
    timestamp=datetime.now().isoformat()
    total_tokens=prompt_tokens+completion_tokens
    cursor.execute("""
        INSERT INTO usage_logs
        (
            timestamp,
            model,
            prompt_tokens,
            completion_tokens,
            total_tokens,
            cost
        )
        VALUES(?,?,?,?,?,?)
    """,(
        timestamp,
        model,
        prompt_tokens,
        completion_tokens,
        total_tokens,
        cost
    ))
    connection.commit()
    connection.close()
def get_today_usage():
    connection=sqlite3.connect(DATABASE)
    cursor=connection.cursor()
    today=date.today().isoformat()
    cursor.execute("""
        SELECT
            COALESCE(SUM(total_tokens),0),
            COALESCE(SUM(cost),0)
        FROM usage_logs
        WHERE DATE(timestamp)=?
    """,(today,))
    result=cursor.fetchone()
    connection.close()
    return{
        "date":today,
        "total_tokens":result[0],
        "total_cost":round(result[1],8)
    }