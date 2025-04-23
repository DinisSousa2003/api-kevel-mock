const TerminusDBClient = require('@terminusdb/terminusdb-client');

//THIS IS NOT WORKING

const dbName = "terminus" //process.argv[2];
const user = "admin" //process.env.TERMINUSDB_USER;
const key = "root" //process.env.TERMINUSDB_KEY;

const client = new TerminusDBClient.WOQLClient("http://localhost:6363/",
    {user:user, key:key});


    async function listDatabases() {
        try {
            const result = await client.getDatabases();
            console.log("Available databases:", result);
        } catch (err) {
            console.error("Could not list databases:", err.message);
        }
    }

    async function getSize() {
        try {
            client.db(dbName)

            // Construct the WOQL query to get the database size
            const WOQL = TerminusDBClient.WOQL;
            const v = WOQL.Vars("size")
            const query = WOQL.size(dbName, v.size);

            // Execute the query
            const result = await client.query(query);

            console.log("Database size:", result);


        } catch (err) {
            console.error("Error querying database:", err);
            process.exit(1);
        }
    }

    //listDatabases();
    
    getSize();