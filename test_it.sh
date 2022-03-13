#!/bin/bash

docker-compose restart todoer-api

docker-compose exec todoer-api pytest
