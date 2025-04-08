import json

class QueryState():

    DROP_TABLE = """ DROP TABLE IF EXISTS customer_state;"""

    CREATE_TABLE = """ CREATE TABLE IF NOT EXISTS customer_state (
                        id TEXT NOT NULL,
                        attributes JSONB NOT NULL,
                        at TIMESTAMP NOT NULL DEFAULT NOW(),
                        PRIMARY KEY (id, at)
                    );"""

    SELECT_USER_AT = """SELECT * FROM customer_state
                    WHERE id = %s AND at <= %s
                    ORDER BY at DESC
                    LIMIT 1;"""
    
    SELECT_USER = """SELECT * FROM customer_state
                    WHERE id = %s AND at <= NOW() 
                    ORDER BY at DESC 
                    LIMIT 1;"""
    
    SELECT_ALL_CURRENT = """SELECT * FROM customer_state
                    WHERE at <= NOW();"""

    
    SELECT_USER_BT_VT_AND_NOW = """SELECT * FROM customer_state
                    WHERE id = %s AND at > %s
                    ORDER BY at;"""
    
    INSERT_WITH_TIME = """INSERT INTO customer_state (id, attributes, at)
                        VALUES (%s, %s, %s)
                        ON CONFLICT (id, at)
                        DO UPDATE SET 
                        attributes = EXCLUDED.attributes"""
    

    
class QueryDiff():
    DROP_TABLE = """ DROP TABLE IF EXISTS customer_diff;"""

    CREATE_TABLE = """ CREATE TABLE IF NOT EXISTS customer_diff (
                        id INTEGER PRIMARY KEY GENERATED ALWAYS AS IDENTITY
                        userId TEXT NOT NULL
                        attributes JSONB NOT NULL,
                        at TIMESTAMP NOT NULL DEFAULT NOW()
                    );"""
    
    INSERT_UPDATE = """INSERT INTO customer_diff (userId, attributes, at)
                        VALUES (%s, %s, %s);"""
    
    SELECT_DIFFS = """SELECT attributes FROM customer_diff
                    WHERE userId = %s
                    ORDER BY at;"""
    
    SELECT_DIFFS_UP_TO_VT = """SELECT attributes, at FROM customer
                    WHERE userId = %s AND at <= %s
                    ORDER BY at;"""""
