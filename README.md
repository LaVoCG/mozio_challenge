## Prerequisites
  - Python 3.8
  - Poetry package manager
  - Docker, if intending to use docker container

## Setup
  - in the root folder of the project run `poetry install`

## Running the service

The service can be run in 2 ways:
  - by running `flask --app ./mozioapi/mozioapi run --host=0.0.0.0`
  - or by running a docker container `docker build -t api . && docker run -it api`


The required test scenario of performing a search, booking and cancellation is set up through a pytest test case.
to perform the scenario, this command should be run in terminal: `poetry run pytest --log-cli-level INFO`