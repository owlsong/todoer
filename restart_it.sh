#!/bin/bash

docker-compose restart todoer-api
sleep 1
docker-compose ps
# docker-compose logs todoer-api
echo 
echo ---------------------------------------------------------------------------------------
echo getting info
curl http://127.0.0.1:8000/todoer/api/v1/info | python -m json.tool
echo 
echo ---------------------------------------------------------------------------------------
echo getting tasks
curl http://127.0.0.1:8000/todoer/api/v1/tasks | python -m json.tool
echo
