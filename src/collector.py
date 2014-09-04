#!/usr/bin/python
__author__ = 'keyz'

import os

POSTGRES_IP = os.environ['POSTGIS21_PORT_5432_TCP_ADDR']
POSTGRES_PORT = os.environ['POSTGIS21_PORT_5432_TCP_PORT']
TWITTER_APP_KEY = os.environ['TWITTER_APP_KEY']
TWITTER_APP_SECRET = os.environ['TWITTER_APP_SECRET']
TWITTER_OAUTH_TOKEN = os.environ['TWITTER_OAUTH_TOKEN']
TWITTER_OAUTH_TOKEN_SECRET = os.environ['TWITTER_OAUTH_TOKEN_SECRET']

COLLECTION_TYPE = os.environ['COLLECTION_TYPE']

TABLE_NAME = os.environ['TABLE_NAME']

from Streamer import SentinelStreamer, StreamForever

twitter_auth = { 'app_key' : TWITTER_APP_KEY,
                'app_secret' : TWITTER_APP_SECRET,
                'oauth_token' : TWITTER_OAUTH_TOKEN,
                'oauth_token_secret' : TWITTER_OAUTH_TOKEN_SECRET }

location =  '-4.4289,51.3484,-2.7684,52.0228'
table_name = TABLE_NAME + "_geo_tweets"
non_geo_table_name = TABLE_NAME + "_tweets"
dbString = "host={0} port={1} dbname=docker user=docker password=docker".format(POSTGRES_IP, POSTGRES_PORT)

stream = SentinelStreamer(twitter_auth=twitter_auth,
                    table_name=table_name,
                    non_geo_table_name=non_geo_table_name,
                    dbString=dbString)


BBOX = os.environ['BBOX']
TERMS = os.environ['SEARCHTERMS']
USERS = os.environ['SEARCHUSERS']


if COLLECTION_TYPE == 'geo':
    StreamForever(stream, locations=BBOX)
elif COLLECTION_TYPE == 'all':
    StreamForever(stream, track=TERMS, locations=BBOX, follow=USERS)
else:
    StreamForever(stream, track=TERMS)

