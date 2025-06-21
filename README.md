# README

## File structure

- `/app`: FastAPI server aplication
- `/aws`: Scripts to run containers on cloud
- `/compose`: Scripts to run tests with docker compose (local, legacy)
- `/dataset`: JSON files with dataset
- `/docs`: Other documents
- `/images`: Images for 
- `/open_source_contributions`: active contributions to the community based on my experience with the databases
- `/output-aws`: Raw data from the AWS tests
- `/scripts`: Scripts for analysis of the dataset

## Run tests

To run the tests, first run the startup script on the `/aws` folder. This uploads all data and installs all necessary software and packages on the EC2 instances.

You may need to change:

- The name of the AWS instances and the path to your private key in the .sh files.
- Change the .env files for each of the databases on `/aws/envs`.

```bash
bash aws/start-all.sh
```

To run the tests use the command below. Alter the parameters of the tests in code, which makes it easier to run multiple tests with a single command. In the end the raw data will be fecthed.

```bash
python3 full-test-aws.py
```

## Analsysis

To make the images, tables and graphs to analyse the tests results, use the `analysis.ipynb` notebook.
