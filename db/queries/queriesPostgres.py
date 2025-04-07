import json

class QueryState():

    CREATE_TABLE = """ CREATE TABLE customer (
                        id TEXT NOT NULL,
                        attributes JSONB NOT NULL,
                        at TIMESTAMP NOT NULL DEFAULT NOW(),
                        PRIMARY KEY (id, at)
                    );"""

    SELECT_ALL_CURRENT_ATTR_VT = """SELECT * FROM customer
                    WHERE id = %s AND at <= %s
                    ORDER BY at DESC
                    LIMIT 1;"""
    
    SELECT_USER_BT_VT_AND_NOW = """SELECT * FROM customer
                    WHERE id = %s AND at > %s
                    ORDER BY at;"""
    
    INSERT_WITH_TIME = """INSERT INTO customer (id, attributes, at)
                        VALUES (%s, %s, %s)
                        ON CONFLICT (id, at)
                        DO UPDATE SET 
                        attributes = EXCLUDED.attributes"""

    
class QueryDiff():
    pass