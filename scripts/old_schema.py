from terminusdb_client.schema import DocumentTemplate

class Stub(DocumentTemplate):
    id: str

"""
hoijnet on TerminusDB discord server:
The JSON datatype would enable you to do this, unfortunately there are some bugs that are not yet ironed out in the schemaless JSON handling and I would not recommend using it yet.
We are looking into how to solve them further ahead. For now the recommendation is to define all schema completely.

You will need to post the migrations to the /migrations endpoint, or if it is without the s, don't remember top of mind. The clients have not added the operations yet I think.
"""