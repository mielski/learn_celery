steps to get started

- install the dependencies with pipenv:
  `pipenv install`
- make sure a redis container is running, see starting redis
- run the command `> celery -A tasks worker --loglevel=INFO -P gevent` in terminal


#### setup docker

Redis  is run using a docker image

`docker run redis -m 6379:6379`

