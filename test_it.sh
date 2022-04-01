#!/bin/bash

docker-compose restart todoer-api
sleep 1

docker-compose exec todoer-api pytest
