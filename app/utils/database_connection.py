import mysql.connector
from ..config import *


class DatabaseConnection:
    def __enter__(self):
        self.conn = mysql.connector.connect(host=MYSQL_HOST, user=MYSQL_USER, passwd=MYSQL_PASSWORD, database=MYSQL_DB)
        self.cursor = self.conn.cursor(buffered=True)
        return self.conn, self.cursor

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.cursor.close()
        self.conn.close()
