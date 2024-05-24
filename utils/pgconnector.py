import os
import psycopg2
from psycopg2 import sql
from dotenv import load_dotenv





class PGConnection:
    def __init__(self, dotenv_path):
        load_dotenv(dotenv_path)
        self.connection = None
        self.cursor = None

    def connect_to_db(self):
        POSTGRES_USER = os.getenv('POSTGRES_USER', 'dev_user')
        POSTGRES_PASSWORD = os.getenv('POSTGRES_PASSWORD', 'placeholder_password')
        POSTGRES_DB = os.getenv('POSTGRES_DB', 'my_database')
        POSTGRES_HOST = os.getenv('POSTGRES_HOST', 'localhost')
        POSTGRES_PORT = os.getenv('POSTGRES_PORT', '5432')
        try:
            # Connect to the PostgreSQL database
            self.connection = psycopg2.connect(
                user=POSTGRES_USER,
                password=POSTGRES_PASSWORD,
                host=POSTGRES_HOST,
                port=POSTGRES_PORT,
                database=POSTGRES_DB
            )
            self.cursor = self.connection.cursor()
            print("Connection to database established successfully")

            

        except (Exception, psycopg2.Error) as error:
            print("Error while connecting to PostgreSQL", error)
    
    def close(self):
        if self.connection:
            self.cursor.close()
            self.connection.close()
            print("PostgreSQL connection closed")



    
if __name__ == "__main__":
    dotenv_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env')
    pgc = PGConnection(dotenv_path)
    pgc.connect_to_db()
    pgc.close()
