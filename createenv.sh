#!/bin/bash
if [[ ! -f settings.conf ]]; then
    echo "No settings file found, copy settings.conf.example to settings.conf"
    exit 1
fi
source settings.conf

docker build -t postwycker .

PSQLCONTAINER=$(docker run --name $INSTANCE_NAME-postgres -d -P keyz182/postgis21)
echo $PSQLCONTAINER
mkdir /tmp/logs
#COLLECTOR_CONTAINER=$(
docker run -d --name $INSTANCE_NAME-collector -v /tmp/logs/:/var/log/supervisor/ --link $INSTANCE_NAME-postgres:postgis21 \
    -e COLLECTION_TYPE="$COLLECTION_TYPE" -e BBOX="$BBOX" -e SEARCHTERMS="$SEARCHTERMS" \
    -e TABLE_NAME="$TABLE_NAME" -e TWITTER_APP_KEY="$TWITTER_APP_KEY" \
    -e TWITTER_APP_SECRET="$TWITTER_APP_SECRET" -e TWITTER_OAUTH_TOKEN="$TWITTER_OAUTH_TOKEN" \
    -e TWITTER_OAUTH_TOKEN_SECRET="$TWITTER_OAUTH_TOKEN_SECRET" postwycker
