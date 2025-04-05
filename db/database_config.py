import mysql.connector
from mysql.connector import Error

def create_connection():
    """Creates and returns a connection to the database."""
    try:
        conn = mysql.connector.connect(
            host="localhost",          # Replace with your host (e.g., 'localhost')
            user="root",               # Your database username
            password="",   # Your database password
            database="smt"             # The name of your database
        )
        if conn.is_connected():
            print("Successfully connected to the database")
            return conn
    except Error as e:
        print(f"Error: {e}")
        return None
