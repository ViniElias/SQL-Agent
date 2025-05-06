import mysql.connector
from mysql.connector import connect
from smolagents import Tool

def mysql_connect(host: str, user: str, password: str, database: str):
    """
    A tool that opens a MySQL connection.
    Args:
        host: The hostname or IP address of the MySQL server.
        user: The username to authenticate with.
        password: The password for the given user.
        database: The database name to connect to.
    Returns:
        A MySQL connection object.
    """
    return connect(host=host, user=user, password=password, database=database)

def mysql_execute(conn, query: str, params: tuple = ()):
    """
    A tool that executes a SQL command (CREATE/INSERT/UPDATE/DELETE) on a MySQL connection.
    Args:
        conn: A MySQL connection object.
        query: A SQL query string to execute.
        params: A tuple of parameters to use with the SQL query.
    """
    cur = conn.cursor()
    cur.execute(query, params)
    conn.commit()


def mysql_fetch(conn, query: str, params: tuple = ()):
    """
    A tool that executes a SELECT query on a MySQL connection and returns the results.
    Args:
        conn: A MySQL connection object.
        query: A SELECT SQL query string to execute.
        params: A tuple of parameters to use with the SQL query.
    Returns:
        A list of tuples containing the query results.
    """
    cur = conn.cursor()
    cur.execute(query, params)
    return cur.fetchall()

mysql_connect_tool = Tool(
    name="mysql_connect",
    func=mysql_connect,
    description="Open a MySQL connection. Args: host, user, password, database."
)

mysql_exec_tool = Tool(
    name="mysql_execute",
    func=mysql_execute,
    description="Execute a SQL command on MySQL (CREATE/INSERT/UPDATE/DELETE). Args: conn, query, params."
)

mysql_fetch_tool = Tool(
    name="mysql_fetch",
    func=mysql_fetch,
    description="Execute a SELECT query on MySQL and return results. Args: conn, query, params."
)