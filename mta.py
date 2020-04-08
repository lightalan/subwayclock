#!/usr/bin/python3
#
# Author: Alan N. Light
#
import time
import time
import time
import time
import time
# Provides a simple interface to train arrival times from the MTA's
# data feeds. A MTA API key is required which must be in the file 'apikey.txt'.
# The interface consists of the getTrainTimes function which takes two
# arguments, the station id's of the uptown and downtown platforms of the
# station we are querying. What will be returned is a 4-tuple which will
# contain:
# 1. A list of the ids of the uptown trains (e.g. "A","1","Q","F", etc.)
# 2. A list of the arrival times of the uptown trains expressed as number
#    of minutes from the current time.
# 3. Same as #1, but for the downtown train
# 4. Same as #2, but for the downtown train
#

from google.transit import gtfs_realtime_pb2
from protobuf_to_dict import protobuf_to_dict
import requests
import datetime
import time
import sys
from datetime import datetime

# Get our API key from file
apikeyfile = 'apikey.txt'
try:
    with open(apikeyfile) as f:APIKey=f.read().rstrip()
except:
    sys.exit("ERROR: Unable to read API key from file %s"%(apikeyfile))

# URLs for each of the MTA's feeds
NQRWfeed = 'https://api-endpoint.mta.info/Dataservice/mtagtfsfeeds/nyct%2Fgtfs-nqrw' # N,Q,R,W 
BDFMfeed = 'https://api-endpoint.mta.info/Dataservice/mtagtfsfeeds/nyct%2Fgtfs-bdfm' # B,D,F,M
S123456feed = 'https://api-endpoint.mta.info/Dataservice/mtagtfsfeeds/nyct%2Fgtfs' # S,1,2,3,4,5,6
ACEHfeed = 'https://api-endpoint.mta.info/Dataservice/mtagtfsfeeds/nyct%2Fgtfs-ace' # A,C,E,H 
Lfeed = 'https://api-endpoint.mta.info/Dataservice/mtagtfsfeeds/nyct%2Fgtfs-l' # L 
Gfeed = 'https://api-endpoint.mta.info/Dataservice/mtagtfsfeeds/nyct%2Fgtfs-g' # G 
JZfeed = 'https://api-endpoint.mta.info/Dataservice/mtagtfsfeeds/nyct%2Fgtfs-jz' # JZ 
Sevenfeed = 'https://api-endpoint.mta.info/Dataservice/mtagtfsfeeds/nyct%2Fgtfs-7' # 7
SIRfeed = 'https://api-endpoint.mta.info/Dataservice/mtagtfsfeeds/nyct%2Fgtfs-si' # SIR

# List of feeds (in order) that we'll check for arrival times.
# The order of this list will be optimized based on the
# feeds most likely to have the trains in which we are interested
feedsToCheck = [NQRWfeed, BDFMfeed, S123456feed, ACEHfeed,
                Lfeed, Gfeed, JZfeed, Sevenfeed, SIRfeed]

# Dictionary of feed "scores." The score will simply be the number of times
# that our desired station was found in a given feed. This will then be used
# to optimize the order of 'feedsToCheck'
feedScores = dict.fromkeys(feedsToCheck,0)

def gettimes(feed, s1, s2):

    uptownTimes = []
    downtownTimes = []
    uptownTrainIDs = []
    downtownTrainIDs = []
    route_id = ""
    
    # Request parameters
    headers = {'x-api-key': APIKey}
    
    # Get the train data from the MTA
    response = requests.get(feed, headers=headers, timeout=30)

    # Parse the protocol buffer that is returned
    feed = gtfs_realtime_pb2.FeedMessage()
    feed.ParseFromString(response.content)

    # Get a list of all the train data
    subway_feed = protobuf_to_dict(feed) # subway_feed is a dictionary
    realtime_data = subway_feed['entity'] # train_data is a list

    # A list of all the arrivals we found for our station in the given feed
    arrivals = []

    # Iterate over each train arrival
    for train in realtime_data:
        # If there is a trip update with a stop time update
        if train.get('trip_update'):
            if (train['trip_update'].get('stop_time_update')):
                # get for each stop time update that is at our stop
                for update in train['trip_update'].get('stop_time_update'):
                    stop_id = update['stop_id']

                    if (stop_id in [s1, s2]):

                        # Get the number of seconds from now to the arrival time
                        elapsed = update['arrival']['time']-time.mktime(datetime.now().timetuple())

                        # If we alredy missed it, skip it
                        if (elapsed < 0):
                            continue
                        
                        route_id = (train['trip_update']['trip']['route_id'])[0]
                        
                        # Calculate minutes and seconds until arrival
                        mins = int(elapsed / 60)
                        secs = int(elapsed % 60)

                        # Round to nearest minute
                        if (secs > 30):
                            mins = mins + 1

                        # Skips zeros
                        if (mins == 0):
                            continue
                        
                        if (stop_id == s1):
                            # Check for dupes and then append
                            if (mins not in uptownTimes):
                                uptownTimes.append(mins)
                                uptownTrainIDs.append(route_id)

                        if (stop_id == s2):
                            if (mins not in downtownTimes):
                                downtownTimes.append(mins)
                                downtownTrainIDs.append(route_id)

    # Sort the results
    if (len(uptownTimes) != 0):
        (uptownTimes, uptownTrainIDs) = tuple(zip(*sorted(zip(uptownTimes, uptownTrainIDs), key=lambda p: p[0])))

    if (len(downtownTimes) != 0):
        (downtownTimes, downtownTrainIDs) = tuple(zip(*sorted(zip(downtownTimes, downtownTrainIDs), key=lambda p: p[0])))

    
    # Return our results as a tuple
    return(uptownTrainIDs, uptownTimes, downtownTrainIDs, downtownTimes)

def getTrainTimes(ourUptownStation, ourDowntownStation):
    global feedsToCheck
    global feedScores

    uptownTrainIDs = []
    uptownTimes = []
    downtownTrainIDs = []
    downtownTimes = []
    
    # Check each of the feeds in turn for trains arriving at our station until
    # we get some results
    for f in feedsToCheck:
        times = gettimes(f, ourUptownStation, ourDowntownStation)
        # If we found our station in the feed, then increment the feed's score and break out
        if (len(times[0]) != 0):
            # Found uptown
            feedScores[f] += 1
            uptownTrainIDs = times[0]
            uptownTimes = times[1]
            if (len(downtownTrainIDs) != 0):
                # Found both
                break
        if (len(times[2]) != 0):
            # Found downtown
            feedScores[f] += 1
            downtownTrainIDs = times[2]
            downtownTimes = times[3]
            if (len(uptownTrainIDs) != 0):
                # Found both
                break


    # Sort 'feedsToCheck' so that we are checking the most likely feeds first
    feedsToCheck = sorted(feedsToCheck, reverse=True, key=lambda p: feedScores[p])
        
    return (uptownTrainIDs, uptownTimes, downtownTrainIDs, downtownTimes)
                    

# Test case, plug in the names of the subway stops you want to test
if __name__ == '__main__':
    if (len(sys.argv) < 3):
        print(getTrainTimes("Q03N","Q03S"))
    else:
        print(getTrainTimes(sys.argv[1],sys.argv[2]))
