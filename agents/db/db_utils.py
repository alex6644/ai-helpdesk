import psycopg2
import tomllib

def load_db_config(config_file="db_config.toml"):
    with open(config_file, "rb") as f:
        config = tomllib.load(f)
    return config["POSTGRES"]

def get_connection():
    db_conf = load_db_config("../db/db_config.toml")
    conn = psycopg2.connect(
        host=db_conf["host"],
        port=db_conf["port"],
        database=db_conf["database"],
        user=db_conf["user"],
        password=db_conf["password"]
    )
    return conn

def insert_email_record(record):
    """
    Erwartet ein Dictionary record mit den Schlüsseln:
      id, sender, subject, body, date_received, status
    """
    conn = get_connection()
    cur = conn.cursor()
    insert_query = """
        INSERT INTO email_queue (id, sender, subject, body, date_received, status)
        VALUES (%(id)s, %(sender)s, %(subject)s, %(body)s, %(date_received)s, %(status)s)
    """
    cur.execute(insert_query, record)
    conn.commit()
    cur.close()
    conn.close()
