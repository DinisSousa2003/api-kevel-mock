import json

class QueryState():

    DROP_TABLE = """ DROP TABLE IF EXISTS customer_state;"""

    CREATE_TABLE = """ CREATE TABLE IF NOT EXISTS customer_state (
                        id TEXT NOT NULL,
                        attributes JSONB NOT NULL,
                        at TIMESTAMP NOT NULL DEFAULT NOW(),
                        PRIMARY KEY (id, at)
                    );"""
    
    CREATE_INDEX = """CREATE INDEX IF NOT EXISTS idx_state_id_at_desc ON customer_state(id, at DESC);"""

    CREATE_INDEX2 = """CREATE INDEX IF NOT EXISTS idx_state_at_brin ON customer_state USING BRIN (at);"""

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
                        id INTEGER PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
                        userId TEXT NOT NULL,
                        attributes JSONB NOT NULL,
                        at TIMESTAMP NOT NULL DEFAULT NOW()
                    );"""
    
    CREATE_INDEX = """CREATE INDEX IF NOT EXISTS idx_customer_diff_userid_at ON customer_diff(userId, at);"""

    CREATE_INDEX2 = """CREATE INDEX IF NOT EXISTS idx_diff_at_brin ON customer_diff USING BRIN (at);"""
    
    INSERT_UPDATE = """INSERT INTO customer_diff (userId, attributes, at)
                        VALUES (%s, %s, %s);"""
    
    SELECT_DIFFS = """SELECT attributes, at FROM customer_diff
                    WHERE userId = %s AND at <= NOW()
                    ORDER BY at;"""
    
    SELECT_DIFFS_UP_TO_VT = """SELECT attributes, at FROM customer_diff
                    WHERE userId = %s AND at <= %s
                    ORDER BY at;"""""
