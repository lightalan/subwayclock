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

NQRWfeednum = '16' # Feed number for N,Q,R,W trains
BDFMfeednum = '21' # Feed number for B,D,F,M trains

# List of feeds (in order) that we'll check for arrival times
feedsToCheck = [NQRWfeednum, BDFMfeednum]

# MTA URL
url = 'http://datamine.mta.info/mta_esi.php'

def gettimes(feednum, s1, s2):

    uptownTimes = []
    downtownTimes = []
    uptownTrainID = ""
    downtownTrainID = ""
    
    # Request parameters
    params = {'key': APIKey, 'feed_id': feednum}
    
    # Get the train data from the MTA
    response = requests.get(url, params=params, timeout=30)

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
                        
                        # Get which train specifically is stopping
                        route_id = train['trip_update']['trip']['route_id']
                        
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
                            uptownTimes.append(mins)
                            if (uptownTrainID == ""):
                                uptownTrainID = route_id

                        if (stop_id == s2):
                            downtownTimes.append(mins)
                            if (downtownTrainID == ""):
                                downtownTrainID = route_id

    # Dedupe
    uptownTimes = list(set(uptownTimes))
    downtownTimes = list(set(downtownTimes))
    
    # Sort the results
    uptownTimes.sort()
    downtownTimes.sort()
                                
    
    # Return our results as a tuple
    return(uptownTrainID, uptownTimes, downtownTrainID, downtownTimes)

def getTrainTimes(ourUptownStation, ourDowntownStation):

    # Check each of the feeds in turn for trains arriving at our station until
    # we get some results
    for f in feedsToCheck:
        times = gettimes(f, ourUptownStation, ourDowntownStation)
        if (times[0] != ''):
            break
        
    return times
                    

# Test case, plug in the names of the subway stops you want to test
if __name__ == '__main__':
    print(getTrainTimes("Q03N","Q03S"))

