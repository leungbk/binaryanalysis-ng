# Scanqueue for BANG

This is a proof of concept scanning queue for BANG. There are a few components:

1. an interface, based on Flask, to upload tasks and query status
2. a task queue


# Components

The following components are used:

* Redis
* Flask
* Celery
* Apache Airflow

## Redis

Redis[1] is a message queue. It is used by Celery.

## Celery

Celery[2] is a distributed task queue. Whenever a file is uploaded via the
webinterface a BANG task is created and put into Celery.

## Flask

Flask[3] is a framework to create microservices.

For BANG the following functionality is needed:

1. upload a firmware file (possibly very large) and submit it for scanning
2. check on the status of an upload/scan

# Running the microservice

### Redis

```
```
## Flask

```
$ export FLASK_APP=bang_scanqueue.py
$ flask run
```

This will launch the webservce, which can then be accessed on the advertised
Flask URL.



# References

[1] https://redis.io/
[2] https://github.com/celery/celery
[3] https://palletsprojects.com/p/flask/