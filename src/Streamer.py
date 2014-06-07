_author__ = 'keyz'
import sys
import psycopg2
import ppygis
import simplejson
from datetime import datetime
import time
from twython import TwythonStreamer

def StreamForever(stream,**kwargs):
    if kwargs is None:
        return
    while True:
        try:
            if locations in kwargs:
                stream.statuses.filter(locations=kwargs['locations'])
            elif track in kwargs:
                stream.statuses.filter(track=kwargs['track'])
        except KeyboardInterrupt:
            print("Ctrl+C Caught, ByeBye!")
            sys.exit()
        except Exception as ex:
            print(ex)
            print("Something broke! Restarting!")

class SentinelStreamer(TwythonStreamer):
    srid = 4326
    init_db = '''-- Enable PostGIS (includes raster)
    --CREATE EXTENSION IF NOT EXISTS postgis;
    -- Enable Topology
    --CREATE EXTENSION IF NOT EXISTS postgis_topology;
    -- Create tweet table
    CREATE TABLE IF NOT EXISTS %(tbl)s (
            id bigint PRIMARY KEY NOT NULL,
            tweet json NOT NULL,
            geometry GEOMETRY(Point,4326) NULL,
            timestamp TIMESTAMP WITH TIME ZONE,
            CONSTRAINT enforce_srid_geometry CHECK (st_srid(geometry) = 4326));
    -- Create spatial index
    CREATE INDEX %(tbl)s_gix ON %(tbl)s USING GIST(geometry);
    CREATE INDEX %(tbl)s_timezone_ix ON %(tbl)s ("timestamp" ASC NULLS LAST);

    CREATE TABLE %(tbl2)s (
            id bigint PRIMARY KEY NOT NULL,
            tweet json NOT NULL,
            timestamp TIMESTAMP WITH TIME ZONE
    );
    CREATE INDEX %(tbl2)s_timezone_ix ON %(tbl2)s ("timestamp" ASC NULLS LAST);
    '''

    '''
    twitter_auth (dict) - dict containing the twitter api auth keys (app_key, app_secret, oauth_token, oauth_token_secret)
    dbString (str)      - Connection string for psycopg2 to connect to postgres.
    table_name (str)    - The name of the table to use in the database
    '''
    def __init__(self, twitter_auth, table_name, non_geo_table_name, dbString):
        super(SentinelStreamer,self).__init__(twitter_auth['app_key'],twitter_auth['app_secret'],
                                              twitter_auth['oauth_token'],twitter_auth['oauth_token_secret'])

        #Check the table_name arg, and substitute into appropriate queries
        if table_name is not None and non_geo_table_name is not None:
            self.table_name = table_name
            self.non_geo_table_name = non_geo_table_name
            self.insert_coords_sql = 'INSERT INTO ' + self.table_name + ' (id,tweet,geometry,timestamp) VALUES (%s,%s,%s,%s);'
            self.insert_sql = 'INSERT INTO ' + self.non_geo_table_name + ' (id,tweet,timestamp) VALUES (%s,%s,%s);'
            self.init_db = self.init_db % {'tbl':self.table_name,'tbl2':self.non_geo_table_name}
        else:
            self.log("No tablename found!")
            exit()

        #Check the dbString arg, then create a connection to the DB. If the table doesn't exist, create it.
        if dbString is not None:
            self.dbString = dbString
            self.conn = psycopg2.connect(self.dbString)
            self.conn.autocommit=True
            self.cur = self.conn.cursor()
            self.cur.execute("select exists(select * from information_schema.tables where table_name=%s)", (self.table_name,))
            if not self.cur.fetchone()[0]:
                print(self.init_db)
                self.cur.execute(self.init_db)
        else:
            self.log("No dbString found!")
            exit()

    '''
    Quick logging method, replace later with proper logging api/library
    '''
    def log(self,line):
        print('%s: %s' %(datetime.now(),line))

    '''
    Called when a tweet is successfully received.
    '''
    def on_success(self, data):
        self.log("Incoming tweet!")
        #Check the tweet contains needed info
        if 'text' in data:
            self.log( data['text'].encode('utf-8'))
        if 'id' in data:
            id = data['id']
        else:
            self.log("No ID found in tweet data, ignoring!")
            return
        if 'created_at' in data:
            date = self.stringToDate(data['created_at'])
        else:
            self.log("Created_at missing")
            return

        #Dump the tweet to a json string for storage in Postgres' Json type
        json = simplejson.dumps(data)

        #If coords are populated in the tweet, use them, otherwise ignore.
        if 'coordinates' in data:
            if data['coordinates'] is not None:
                self.log("It's Geotagged!")
                c = data['coordinates']
                #Create the proper ppygis object and set srid so that it gets formated for postgres properly
                point = ppygis.Point(c['coordinates'][0],c['coordinates'][1])
                point.srid = self.srid
                try:
                    self.cur.execute(self.insert_coords_sql, (id, json, point,date))
                except Exception as e:
                    self.log("Exception encountered wrtiting tweet")
                    self.log(e)
                return

        #Write non geotagged tweet
        try:
            self.cur.execute(self.insert_sql, (id, json,date))
        except Exception as e:
            self.log("Exception encountered wrtiting tweet")
            self.log(e)


    def on_error(self, status_code, data):
        if status_code is not 200:
            self.log( status_code)
        # Want to stop trying to get data because of the error?
        # Uncomment the next line!
        # self.disconnect()

    '''
    Convert Tweets 'created_at' date string to python date.
    '''
    def stringToDate(self,date_str):
        time_struct = time.strptime(date_str, "%a %b %d %H:%M:%S +0000 %Y")#Tue Apr 26 08:57:55 +0000 2011
        return datetime.fromtimestamp(time.mktime(time_struct))

