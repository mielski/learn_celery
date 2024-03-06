# Introduction

This is my learning repository on celery best practices and patterns

## Case: local and remove runs with groups

One of the concepts in this branch is to use group() workflows with celery for efficiency, but making an orchestration which
still allows a developer to run this locally without celery.

Second concept it shows is how to use caching to initialize workers.

## 

- install the dependencies with pipenv:
  `pipenv install`
- make sure a redis container is running, see starting redis
- run the command `> celery -A tasks worker --loglevel=INFO -P gevent` in terminal


#### setup docker

Redis  is run using a docker image

`docker run redis -m 6379:6379`

