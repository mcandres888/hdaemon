import pafy
import couchdb
import urllib
import urllib2
import json
import requests
import re
import time
import sys
import shutil
import os   

import xmpp, time, datetime

SERVER = "neural.thousandminds.com"
USER = "youtube_downloader01@neural.thousandminds.com"
PASS = "dondon"
jid = xmpp.JID(USER)
mcandres = xmpp.JID('mcandres@neural.thousandminds.com')
laalmonte = xmpp.JID('laalmonte@neural.thousandminds.com')

connection = xmpp.Client(jid.getDomain())
connection.connect(server=(SERVER,5222))
connection.auth(USER, PASS, "Daemon")
connection.sendInitPresence()



BASE = "https://hunterzero.iriscouch.com"
VIDEOS_DESIGN  = BASE + "/videos/_design/query/_view/"
BY_YOUTUBE = VIDEOS_DESIGN + "byYoutubeNotUpdated?reduce=false&limit=5"

COUCH_SERVER = couchdb.client.Server(BASE)
VID_DB = COUCH_SERVER['videos']
    
#BASE_DIR = "/Users/mcandres/sandbox/python_sandbox/youtube_downloads/"
BASE_DIR = "/mnt/storage/mcandres/utorrent/youtube/"
    
def infoLog(data):
    try:
        os.system("echo '%s'" % data)
    except UnicodeEncodeError:
        os.system("echo 'Unicode Error'" )
   

def getTimestamp () :
    ts = time.time()
    return  datetime.datetime.fromtimestamp(ts).strftime('%Y-%m-%d %H:%M:%S')


def sendToChat (data):
    try:
        connection.send(xmpp.protocol.Message(mcandres, '[' + getTimestamp() + '] ' + str(data), typ='chat'))
        connection.send(xmpp.protocol.Message(laalmonte, '[' + getTimestamp() + '] ' + str(data), typ='chat'))
    except UnicodeEncodeError:
        connection.send(xmpp.protocol.Message(mcandres, '[' + getTimestamp() + ']Unicode Error ' , typ='chat'))

def queryDesignView( design_url ):
    retval = urllib2.urlopen(design_url).read()
    temp = json.loads(retval)
    return temp['rows']



def createInfoFile (data, video, stream):
    doc_id = data['id']
    infoLog("111 %s" % doc_id)
    video_dir = BASE_DIR + doc_id
    TEMP_DOC = VID_DB[doc_id]
    infoLog("222")
    TEMP_DOC['title'] = video.title
    TEMP_DOC['viewcount'] = video.viewcount
    TEMP_DOC['author'] = video.author
    TEMP_DOC['length'] = video.length
    TEMP_DOC['videoid'] = video.videoid
    infoLog("333")
    try:
        TEMP_DOC['category'] = video.category
        TEMP_DOC['description'] = video.description
        TEMP_DOC['dislikes'] = video.dislikes
        TEMP_DOC['duration'] = video.duration
        TEMP_DOC['keywords'] = video.keywords

        TEMP_DOC['likes'] = video.likes
        TEMP_DOC['published'] = video.published
        TEMP_DOC['rating'] = video.rating
        TEMP_DOC['thumb'] = video.thumb
        TEMP_DOC['bigthumb'] = video.bigthumb
        TEMP_DOC['bigthumbhd'] = video.bigthumbhd
        TEMP_DOC['stream_url'] = stream.url
        TEMP_DOC['stream_url_https'] = stream.url_https
        TEMP_DOC['stream_bitrate'] = stream.bitrate
        TEMP_DOC['stream_dimensions'] = stream.dimensions
        TEMP_DOC['stream_extension'] = stream.extension
        TEMP_DOC['stream_mediatype'] = stream.mediatype
        TEMP_DOC['stream_quality'] = stream.quality
        TEMP_DOC['stream_resolution'] = stream.resolution
        TEMP_DOC['stream_resolution'] = stream.resolution

    except:
        print "error"
    infoLog("333")
    if os.path.isdir(video_dir):
        shutil.rmtree(video_dir)
    infoLog("444")
    os.mkdir(video_dir)
    infoLog("Downloading file %s" % video_dir + "/video.mp4")
    stream.download(video_dir + "/video.mp4")

    if video.bigthumb != "":
        urllib.urlretrieve (video.bigthumb, video_dir + "/bigthumb.jpg")

    if video.bigthumbhd != "":
        urllib.urlretrieve (video.bigthumbhd, video_dir + "/bigthumbhd.jpg")
   

    urllib.urlretrieve (video.thumb, video_dir + "/thumb.jpg")
    TEMP_DOC['retrieved'] = 1
    json_string = json.dumps(TEMP_DOC,sort_keys=True, indent=4)
    f = open(video_dir + '/data.json', 'w')
    f.write(json_string)
    f.close()
   
    sendToChat("%s downloaded with id %s" % (video.title,doc_id))
    sendToChat("http://192.168.1.8/mc/youtube/%s/video.mp4" % (doc_id))
    VID_DB[doc_id] = TEMP_DOC



def checkVideoStream ( video ):
    # check if there is mp4
    mp4_list = []
    mp4_380 = []
    for s in video.streams:
        if s.extension == "mp4":
            mp4_list.append(s)
            if s.dimensions[1] == 380 or s.dimensions[1] == 360:
                mp4_380.append(s)
         


    final_res = ""
    # now get the resolution
    if len(mp4_380) > 0:
        final_res =  mp4_380[0]
    elif len(mp4_list) > 1:
        final_res =  mp4_list[1]
    elif len(mp4_list) == 1:
        final_res = mp4_list[0]
    else:
        final_res = 1
    final_res = video.getbest()
    return final_res




def youtubeDownload(data):
    # check for streams, make sure that we have 380p mp4 or lower streams,
    # else do not download
    print data
    url = data['key'].replace("^", "&")
    try:
        video = pafy.new(url)
        print video
        # get streams
        stream = checkVideoStream(video)
        if stream != "":
            infoLog("Downloading stream %s" % stream.quality)
            # download stream and its data
            createInfoFile (data, video, stream)
        else:
            infoLog("Error, no stream available")
    except ValueError:
        print "value error"
        doc_id = data['id']
        TEMP_DOC = VID_DB[doc_id]
        TEMP_DOC['retrieved'] = 3
        VID_DB[doc_id] = TEMP_DOC
    


def main():
    data_list = queryDesignView( BY_YOUTUBE )
    for data in data_list:
        print data
        try:
            youtubeDownload ( data )
        except IOError:
            doc_id = data['id']
            infoLog( "IO error doc_id = %s" % doc_id)
            TEMP_DOC = VID_DB[doc_id]
            TEMP_DOC['retrieved'] = 0
            VID_DB[doc_id] = TEMP_DOC
        time.sleep(3)






if __name__ == "__main__":
    sendToChat("I am now online")
    while(1):
        main()
        time.sleep(5)


