#!/bin/sh

git pull origin master
iID=`basename "$PWD"`
contID=`docker inspect --format="{{.Id}}" ${iID}`
echo $contID
if [[ $contID ]]; then
    docker stop $iID;
    docker rm $contID;
fi

#docker rmi $iID
docker build -t $iID .
