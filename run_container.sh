#!/bin/sh
APP_NAME="gmsh"
VERSION="1.3"

WORKDIR=$(pwd)

docker build -t ${APP_NAME}:${VERSION} .

docker run -v ${WORKDIR}/db:/db -v ${WORKDIR}/config:/gmsh/config:ro \
--env-file ./deploy.env -d --name ${APP_NAME} ${APP_NAME}:${VERSION}