# Issue on size function
Published: https://github.com/terminusdb/terminusdb/issues/2175

**Describe the bug**
The following error appears when using the size function:

```
'api:message': "Error: existence_error(file,'/app/terminusdb/storage/dbb5e/b5ef665ca9cf43244d0fdd1028e8eeb70d8ff958.larch')\n"
```

The size function is looking for the .larch files at dbXXX instead of db/XXX where they are stored.

**To Reproduce**
The problem was found by running this small script on Javascript client

```js
async function getSize() {
        try {
            client.db(dbName)

            // Construct the WOQL query to get the database size
            const WOQL = TerminusDBClient.WOQL;
            const v = WOQL.Vars("size")
            const query = WOQL.size(`${user}/${dbName}`, v.size);

            // Execute the query
            const result = await client.query(query);
            const bytes = result["bindings"][0]["size"]["@value"]

            console.log("Database size:", bytes, "bytes");

            return bytes
        } catch (err) {
            console.error("Error querying database:", err);
            process.exit(1);
        }
    }
```

**Expected behavior**
Was expected to return the size of the database. By creating symlinks in the container between dbXXX and db/XXX the problem was fixed.


**Info (please complete the following information):**
 - OS: Windows10 + WSL2
 - using Docker directly

**Additional context**
Reported on Discord 
