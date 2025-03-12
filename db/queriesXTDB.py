import json

class Query():

    SELECT_USER = """SELECT c.*, _valid_from, _valid_to 
                        FROM customer AS c 
                        WHERE _id = %s"""

    SELECT_USER_WITH_VT = """SELECT c.*, _valid_from, _valid_to FROM customer
                    FOR VALID_TIME AS OF %s AS c
                    WHERE _id = %s"""

    SELECT_USER_BT_VT_AND_NOW = """SELECT c.*, _valid_from, _valid_to FROM customer
                    FOR VALID_TIME FROM %s TO CURRENT_TIMESTAMP AS c
                    WHERE _id = %s"""
    
    SELECT_ALL_CURRENT = """SELECT * FROM customer"""

    #NOT WORKING
    SELECT_NESTED_ARGUMENTS = query = """SELECT c._id, c.attributes, c.attributes['f86a8b7ef428c89ed1f4d36cdf38b5e4'] FROM customer AS c"""

    SELECT_ALL_WITH_TIMES = """SELECT c.*, _valid_from, _valid_to, _system_from, _system_to FROM customer FOR ALL SYSTEM_TIME FOR ALL VALID_TIME AS c"""

    def PATCH_WITH_TIME(attributes):
        return f"""PATCH INTO customer FOR VALID_TIME FROM %s RECORDS {{_id: %s, attributes: {json.dumps(attributes)}}};"""

