#!/usr/bin/python3

from tkinter import *
from mta import *
import datetime;
from argparse import ArgumentParser
import os
import glob

# Command-line arguments
aparse = ArgumentParser()
aparse.add_argument('-f','--fullscreen', action="store_true", default=False,
                    help="fullscreen")
aparse.add_argument('-u','--uptownstation', action="store", default="Q03N",
                    help="Uptown Station")
aparse.add_argument('-d','--downtownstation', action="store", default="Q03S",
                    help="Downtown Station")
aparse.add_argument('-U','--uptowndescription', action="store",
                    default="Uptown to 96th St.",
                    help="Uptown Station Description")
aparse.add_argument('-D','--downtowndescription', action="store",
                    default="Downtown and Brooklyn",
                    help="Downtown Station Description")



args = aparse.parse_args()

# Our stations uptown and downtown, at 72nd and 2nd
ourUptownStation = args.uptownstation
ourDowntownStation = args.downtownstation

# Platform descriptions of the above
uptownDescription = args.uptowndescription
downtownDescription = args.downtowndescription

# Font
fontName = "sans"

# A minute's worth of milliseconds
oneMinute = 60000

# Interval in minutes between MTA data fetches
fetchInterval = 3

# List of uptown and downtown train arrival times, in minutes
uptownMinutes = []
downtownMinutes = []

# Which train is running (Q, M, etc.) uptown and downtown
uptownTrain = ""
downtownTrain = ""

# Format a list of arrival times into a string for display
def formatMinutes(mList):

    # If the list is empty, return empty string
    if (len(mList) == 0):
        return("")

    # Slice off the first three or four times and turn them into a
    # comma-separated list

    # If the first item in the list is two digits, then only return
    # the first three items, otherwise the first four. This is so as
    # to not wind up with a string too long to display.
    
    n = 4
    if (mList[0] > 9):
        n = 3
    
    return(" " + ', '.join(map(str, mList[:n])))

# Decrement each minute on a list of arrival times, roll off any 0's
def decList(l):
    return([i-1 for i in l if i-1 > 0])

# Will be called every minute
def callBack():
    global minuteCounter
    global uptownMinutes
    global downtownMinutes
    global topImage
    global bottomImage
    global uptownTrain
    global downtownTrain
    global topText
    global bottomText
    
    # Decrement all the arrival times by a minute (unless it's the first
    # time through)
    if (minuteCounter != 0):
        uptownMinutes = decList(uptownMinutes)
        downtownMinutes = decList(downtownMinutes)
        
    # If it's time to fetch fresh MTA data, do so (and update the images)
    if ((minuteCounter % fetchInterval) == 0):

        try:
            (uptownTrain,
             uptownMinutes,
             downtownTrain,
             downtownMinutes) = getTrainTimes(ourUptownStation,
                                           ourDowntownStation)
            
            # If we successfully got MTA API data, set our text to black
            topText.config(fg="black")
            bottomText.config(fg="black")
        except:
            # If the last MTA API call failed, set our text to red
            topText.config(fg="red")
            bottomText.config(fg="red")
            
            # If the API called failed, then bump the minute counter
            # down. This will force another API call on the next
            # firing of the callback.
            minuteCounter -= 1

        # Set the images to the uptown and downtown trains    
        try:
            topImage['image'] = images[uptownTrain]
        except:
            topImage['image'] = images['unknown']

        try:
            bottomImage['image'] = images[downtownTrain]
        except:
            bottomImage['image'] = images['unknown']
            
    # Update the display of the arrival times
    topString.set(formatMinutes(uptownMinutes))
    bottomString.set(formatMinutes(downtownMinutes))

    # Increment our minute counter
    minuteCounter += 1

    # See 'ya again in a minute
    m.after(oneMinute,callBack)


# Create main application window
m = Tk()

# Are we fullscreen
if (args.fullscreen):
    m.attributes("-fullscreen", True)
    m.overrideredirect(1)
    
displayWidth = m.winfo_screenwidth()
displayHeight = m.winfo_screenheight()

# Get display DPI
dpi = int(m.winfo_pixels('1i'))

# Calculate points per pixel
ppx = dpi / 72

# Font size of time text should be 10% of screen height
timeTextFontSize = int((displayHeight * 0.10) * ppx)

# Label font size should be 5% of screen height
labelFontSize = int((displayHeight * 0.05) * ppx)

# Make our background white
m.configure(background='white')

# Target size of images is 37.5% of display height
imageSize = int(displayHeight * 0.375)


# Map train letters to images. Scale the images as necessary. The results
# of scaling the images are not great, it's STRONGLY recommended that you
# create images which are already of the correct size (37.5% of display height).

images = {}

# Grab each PNG in the icons subdirectory
for f in (glob.glob('icons%s*.png'%(os.sep))):

    # Index on the basename of the PNG file. For example the "A" train will
    # have its image in the file icons/A.png
    l = os.path.basename(os.path.splitext(f)[0])
    images[l] = PhotoImage(file=f)

    # If the image is not square, we're just not going to deal with it.
    if (images[l].height() != images[l].width()):
        raise Exception("Image icons%s%s.png is not square"%(os.sep,l))

    # Are we scaling down?
    if ((images[l].height() > imageSize)):
        scale = int(1 / (imageSize/images[l].width()))
        images[l] = images[l].subsample(scale, scale)

    # Are we scaling up?
    if ((images[l].height() < imageSize)):
        scale = int(imageSize/images[l].width())
        images[l] = images[l].zoom(scale, scale)


# Uptown platform name
Label(m,
      font=(fontName,labelFontSize),
      text=uptownDescription).grid(row=0,
                                   column=0,
                                   columnspan=2,
                                   sticky=W)

# Uptown train image
topImage = Label(m)

topImage.grid(row=1, column=0)

# Label which displays uptown arrival times
topString = StringVar()
topText = Label(m,
                font=(fontName, timeTextFontSize),
                textvariable=topString)
topText.grid(row=1, column=1, sticky=W)

# Draw horizontal line seperating uptown/downtown times
lineMargin = 20
c = Canvas(m,width=displayWidth,
           height=lineMargin,
           bd=0,
           highlightthickness=0,
           relief='ridge')
c.grid(row=2, column=0,columnspan=2, sticky="ew")
c.create_line(0,lineMargin,displayWidth,lineMargin,width=3)

# Downtown platform name
Label(m,
      font=(fontName,labelFontSize),
      text=downtownDescription).grid(row=3,
                                     column=0,
                                     columnspan=2,
                                     sticky=W)

# Downtown train image
bottomImage = Label(m)
bottomImage.grid(row=4, column=0)

# Label which displays downtown arrival times
bottomString = StringVar()
bottomText = Label(m,
                   font=(fontName,timeTextFontSize),
                   textvariable=bottomString)
bottomText.grid(row=4, column=1, sticky=W)

# Make all widgets have the same bg color as the main window
for c in m.winfo_children():
    c.configure(background=m['background'])

# Counts the number of minutes we've been running
minuteCounter = 0


# Kick off the callback
callBack()

# Run the UI
m.mainloop()



