- SIZE OF DATABASE VOLUME: Get it to work between containers
- CHANGE XTDB2 from local tmp to volume SIZE FUNCTION
- Script to set up on AWS

- BUGFIX: Think of what is needed to update the future states on the most-recent and older attibutes: OLDER needs to know the value on the last state (not the value of the update). MOST-RECENT needs to know the timestamp of the update added the value there (tuple value timestamp). (does not affect the outcome/test result, just correctness)

- Postgres is not persisting (lose the data on reload)
- Time between updates not per client on analysis
- Missing test for all terminus (state + others missing lock to ensure correctness)
- Script to read the averages and draw a plot for each database
- Thesis writing