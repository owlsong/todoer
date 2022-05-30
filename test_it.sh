#!/bin/bash

echo 
echo ================================
echo --- running Todoer API tests ---
echo ================================
echo 

docker-compose restart todoer-api
sleep 1

docker-compose exec todoer-api pytest
