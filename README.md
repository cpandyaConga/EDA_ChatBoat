# Create a Data API for Snowflake Data using Python and Flask
Technologies used: [Snowflake](https://snowflake.com/), [Python](https://www.python.org/), 
[Flask](https://palletsprojects.com/p/flask/), [Anaconda](https://www.anaconda.com/)

This project demonstrates how to build a custom REST API powered by Snowflake. 
It uses a simple Python Flask API service running locally. Connectivity is made to 
Snowflake via key pair authentication.

## Requirements:
* Snowflake account
* Snowflake user with
  * SELECT access to the `SNOWFLAKE_SAMPLES.TPCH_SF10.ORDERS` table
  * USAGE access on a warehouse
* Python 3.8
* Anaconda (or Miniconda)

## Configuration
### Python
Using `conda`, create a new environment from the `conda_environment.yml` file:
```
conda env create -f conda_environment.yml
```

This environment will be created with all the necessary prerequisite packages.
It will be activated once created. If you need to activate the environment
again at some other time, you can do so:
```
conda activate pylab
```

### Snowflake
Use the template in `config.py.example` to enter your information in JSON format:
* account
* user
* password
* Snowflake warehouse

See [Snowflake documentation](https://docs.snowflake.com/en/developer-guide/python-connector/python-connector-api#label-account-format-info) for information on how to find your account identifier.

## Running
To start the server, from the `src/` directory, run:
```
python app.py
```



