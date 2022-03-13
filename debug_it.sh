#!/bin/bash

docker-compose restart todoer-api

docker-compose logs todoer-api -f|grep INFO

