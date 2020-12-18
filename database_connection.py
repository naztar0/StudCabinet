import mysql.connector
import constants as c


class DatabaseConnection:
    def __enter__(self):
        self.conn = mysql.connector.connect(host=c.host, user=c.user, passwd=c.password, database=c.db)
        self.cursor = self.conn.cursor(buffered=True)
        return self.conn, self.cursor

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.cursor.close()
        self.conn.close()
