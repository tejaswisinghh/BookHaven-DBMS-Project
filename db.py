import logging
from contextlib import contextmanager
from config import Config

logger = logging.getLogger(__name__)

# Determine available MySQL connector
CONNECTOR_TYPE = None
try:
    import mysql.connector
    from mysql.connector import Error as MySQLError
    CONNECTOR_TYPE = "mysql.connector"
except ImportError:
    try:
        import pymysql
        import pymysql.cursors
        from pymysql import Error as MySQLError
        CONNECTOR_TYPE = "pymysql"
    except ImportError:
        CONNECTOR_TYPE = None


def get_raw_connection(include_database=True):
    """
    Establish a connection to the MySQL server using whichever
    connector is available (mysql.connector or PyMySQL).
    """
    if CONNECTOR_TYPE is None:
        raise RuntimeError(
            "No MySQL driver found! Please install either 'mysql-connector-python' or 'PyMySQL':\n"
            "pip install mysql-connector-python"
        )

    cfg = Config.get_db_config()
    db_name = cfg["database"] if include_database else None

    if CONNECTOR_TYPE == "mysql.connector":
        conn_params = {
            "host": cfg["host"],
            "port": cfg["port"],
            "user": cfg["user"],
            "password": cfg["password"],
            "autocommit": False,
        }
        if db_name:
            conn_params["database"] = db_name
        return mysql.connector.connect(**conn_params)

    elif CONNECTOR_TYPE == "pymysql":
        conn_params = {
            "host": cfg["host"],
            "port": cfg["port"],
            "user": cfg["user"],
            "password": cfg["password"],
            "autocommit": False,
            "cursorclass": pymysql.cursors.DictCursor,
        }
        if db_name:
            conn_params["database"] = db_name
        return pymysql.connect(**conn_params)


@contextmanager
def get_db_cursor(commit=False):
    """
    Context manager providing a database cursor with dictionary output.
    Automatically commits on success if commit=True, and rolls back on exception.
    Always cleans up cursor and connection.
    """
    conn = get_raw_connection(include_database=True)
    cursor = None
    try:
        if CONNECTOR_TYPE == "mysql.connector":
            cursor = conn.cursor(dictionary=True)
        else:
            cursor = conn.cursor()

        yield cursor, conn

        if commit:
            conn.commit()
    except Exception as exc:
        if conn:
            try:
                conn.rollback()
            except Exception:
                pass
        logger.exception("Database transaction error: %s", exc)
        raise exc
    finally:
        if cursor:
            try:
                cursor.close()
            except Exception:
                pass
        if conn:
            try:
                conn.close()
            except Exception:
                pass


def check_db_health():
    """
    Diagnose MySQL connection and verify expected tables exist.
    Returns a dictionary of diagnostic information.
    """
    result = {
        "connected": False,
        "connector": CONNECTOR_TYPE or "None installed",
        "database": Config.DB_NAME,
        "host": f"{Config.DB_HOST}:{Config.DB_PORT}",
        "user": Config.DB_USER,
        "tables_found": [],
        "missing_tables": [],
        "message": ""
    }

    if CONNECTOR_TYPE is None:
        result["message"] = "No MySQL driver installed. Run: pip install mysql-connector-python"
        return result

    try:
        with get_db_cursor(commit=False) as (cursor, conn):
            cursor.execute("SELECT DATABASE() AS current_db, VERSION() AS version;")
            row = cursor.fetchone()
            result["connected"] = True
            result["server_version"] = row["version"] if row else "Unknown"

            # Check expected tables
            cursor.execute("SHOW TABLES;")
            tables = [list(r.values())[0] for r in cursor.fetchall()]
            result["tables_found"] = tables

            expected = ["Authors", "Books", "Customers", "Orders"]
            found_lower = [t.lower() for t in tables]
            missing = [t for t in expected if t.lower() not in found_lower]
            result["missing_tables"] = missing

            if missing:
                result["message"] = (
                    f"Connected to MySQL, but missing tables: {', '.join(missing)}. "
                    "Run 'init_db.sql' to initialize schema and sample data."
                )
            else:
                result["message"] = "Database fully connected and initialized!"
    except Exception as e:
        result["connected"] = False
        result["message"] = str(e)

    return result
