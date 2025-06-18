import json

class QueryState():

    SELECT_USER = """SELECT c.*, _valid_from, _valid_to 
                        FROM customer_state AS c 
                        WHERE _id = %s;"""

    SELECT_USER_WITH_VT = """SELECT c.*, _valid_from, _valid_to FROM customer_state
                    FOR VALID_TIME AS OF %s AS c
                    WHERE _id = %s;"""
    
    SELECT_ALL_CURRENT_ATTR_VT = """SELECT * FROM customer_state
                    FOR VALID_TIME AS OF %s
                    WHERE _id = %s;"""

    SELECT_USER_BT_VT_AND_NOW = """SELECT *, _valid_from, _valid_to FROM customer_state
                    FOR ALL VALID_TIME
                    WHERE _id = %s AND _valid_from > %s
                    ORDER BY _valid_from;"""
    
    SELECT_ALL_CURRENT = """SELECT * FROM customer_state;"""

    SELECT_NESTED_ARGUMENTS = """SELECT c._id, (c.attributes)."7a9ec0f97cd6f47b044e72673d493a68" FROM customer_state FOR ALL SYSTEM_TIME FOR ALL VALID_TIME AS c;"""

    SELECT_ALL_WITH_TIMES = """SELECT c.*, _valid_from, _valid_to, _system_from, _system_to FROM customer_state FOR ALL SYSTEM_TIME FOR ALL VALID_TIME AS c;"""

    SELECT_ALL_VALID_WITH_TIMES = """SELECT c.*, _valid_from, _valid_to FROM customer_state FOR ALL VALID_TIME AS c;"""

    ERASE_ALL = """ERASE FROM customer_state;"""

    def SELECT_ATTR(attr, id):
        return f"""SELECT (c.attributes)."{attr}" FROM customer_state AS c WHERE _id = {id};"""
    
    def SELECT_ATTR_TIME(attr):
        return f"""SELECT (c.attributes)."{attr}" FROM customer_state
             FOR VALID_TIME AS OF %s AS c 
             WHERE _id = %s;"""

    INSERT_WITH_TIME = """INSERT INTO customer_state RECORDS {_id: %s, attributes: %s, _valid_from: %s};"""
    
    INSERT_WITH_TIME_PERIOD = """INSERT INTO customer_state RECORDS {_id: %s, attributes: %s, _valid_from: %s, _valid_to: %s};"""

    SELECT_SIZE = """SELECT sum(data_file_size) FROM xt.trie_stats WHERE trie_state = 'live';"""
    
class QueryDiff():

    INSERT_UPDATE = """INSERT INTO customer_diff RECORDS {_id: %s, userId: %s, attributes: %s}"""
    
    INSERT_WITH_TIME = """INSERT INTO customer_diff RECORDS {_id: %s, userId: %s, attributes: %s, _valid_from: %s}"""
    
    SELECT_DIFFS_USER_UP_TO_VT = """SELECT attributes, _valid_from FROM customer_diff
                    FOR VALID_TIME AS OF %s
                    WHERE userId = %s
                    ORDER BY _valid_from;"""
    
    SELECT_DIFFS_USER = """SELECT attributes, _valid_from FROM customer_diff
                    WHERE userId = %s
                    ORDER BY _valid_from;"""
    
    SELECT_ALL_USERS = """SELECT DISTINCT userId
                        FROM customer_diff"""
    
    SELECT_ALL_DIFFS = """SELECT userId, attributes, _valid_from
                        FROM customer_diff
                        ORDER BY userId, _valid_from;"""
    
    ERASE_ALL = """ERASE FROM customer_diff;"""