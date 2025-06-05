# README

## File structure

- `/docs`: .md files with instructions
- `/db`: .py to ineract with the databases
- `/envs`: env vars for databases
- `/scripts`: .sh scripts to start the database (docker) and other test scripts
- `/open_source_contributions`: active contributions to the community based on my experience with the databases
- `/imports`: files with models and classes to be imported by other files
- `/dataset`: where the files should be. Uncommited to github to reduce size of repo

## Run tests

```bash
python3 full-test.py <terminus|xtdb2|postgres>
```

## How to get size of DB

- Postgres: Use the endpoint users/\<mode\>/db/size. More on the functions used in ([Postgres Documentation](https://www.postgresql.org/docs/current/functions-admin.html#FUNCTIONS-ADMIN-DBSIZE))
- TerminusDB: Use the docker volume size: `docker run --rm -v terminusdb-data:/data alpine du -sh /data` to get full size and size() to get in-memory size of layer (need to run the symlinks script first)
- XTDB: TODO

## Postgres

| Folder / File | Purpose |
|:---|:---|
| **base/** | Main directory for user databases (actual tables and indexes are stored here). One subfolder per database (named by OID). |
| **global/** | Cluster-wide (shared) data: system catalogs like `pg_database`, `pg_authid`, etc. |
| **pg_commit_ts/** | Stores commit timestamps if `track_commit_timestamp` is enabled. |
| **pg_dynshmem/** | Dynamic shared memory files, used internally by server processes for coordination. |
| **pg_hba.conf** | Client authentication (host-based access) configuration file. |
| **pg_ident.conf** | Maps system usernames to database usernames (for authentication). |
| **pg_logical/** | Data for logical replication (publications/subscriptions). |
| **pg_multixact/** | Manages multi-transaction IDs (e.g., multiple transactions sharing locks). |
| **pg_notify/** | Stores LISTEN/NOTIFY information (asynchronous notifications). |
| **pg_replslot/** | Replication slots to prevent replicas from falling behind. |
| **pg_serial/** | Stores information about serializable transactions (for Serializable isolation level). |
| **pg_snapshots/** | Stores exported snapshots for Repeatable Read transactions. |
| **pg_stat/** | Persistent statistics about database activity (table accesses, etc.). |
| **pg_stat_tmp/** | Temporary statistics files (cleared on restart). |
| **pg_subtrans/** | Helps track subtransactions (nested transactions). |
| **pg_tblspc/** | Symlinks to other locations for storing data (tablespaces). |
| **pg_twophase/** | Files for two-phase commit transactions (prepared transactions). |
| **PG_VERSION** | Simple text file containing the PostgreSQL major version (e.g., "16"). |
| **pg_wal/** | Write-Ahead Log (WAL) files for crash recovery and replication. |
| **pg_xact/** | Transaction commit/abort status files (formerly `pg_clog`). |
| **postgresql.auto.conf** | Settings modified automatically by `ALTER SYSTEM` commands. |
| **postgresql.conf** | Main server configuration file for parameters (edited manually). |
| **postmaster.opts** | Internal file with startup options used by the `postmaster` process. |

## Characteristics (TODO)

Updates to the past
Updates to the future (past now)
Query present
Query past
Query future
Immutable
Bitemporal
