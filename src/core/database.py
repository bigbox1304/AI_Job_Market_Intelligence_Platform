import psycopg2
from psycopg2 import pool

# =========================================
# CONFIG DB
# =========================================

import os

DB_CONFIG = {
    "host": os.getenv("JOB_DB_HOST", "job-postgres"),
    "database": os.getenv("JOB_DB_NAME", "jobdb"),
    "user": os.getenv("JOB_DB_USER", "jobuser"),
    "password": os.getenv("JOB_DB_PASS", "jobpass123"),
    "port": int(os.getenv("JOB_DB_INTERNAL_PORT", os.getenv("JOB_DB_PORT", 5432))),
}

# =========================================
# LAZY CONNECTION POOL
# =========================================

connection_pool = None


def get_pool():
    global connection_pool

    if connection_pool is None:
        connection_pool = psycopg2.pool.SimpleConnectionPool(
            minconn=1,
            maxconn=10,
            **DB_CONFIG
        )

    return connection_pool


# =========================================
# GET CONNECTION
# =========================================

def get_db():
    try:
        pool = get_pool()
        conn = pool.getconn()
        return conn
    except Exception as e:
        print("Error getting DB connection:", e)
        raise


# =========================================
# RELEASE CONNECTION
# =========================================

def release_db(conn):
    try:
        pool = get_pool()
        pool.putconn(conn)
    except Exception as e:
        print("Error releasing DB connection:", e)


# =========================================
# CLOSE ALL
# =========================================

def close_all_connections():
    global connection_pool
    if connection_pool:
        connection_pool.closeall()
