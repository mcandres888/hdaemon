import couchdb
import urllib
import urllib2
import json
import requests
import re
import time
import sys
import os
import shutil
import datetime

BASE = "https://hunterzero.iriscouch.com"
VIDEOS_DESIGN  = BASE + "/videos/_design/query/_view/"
BY_URL = VIDEOS_DESIGN + "byUrl?reduce=false"
BY_DATA_NOT_UPDATED = VIDEOS_DESIGN + "byDataNotUpdated?reduce=false&limit=5"
BY_UPDATED_DATA = VIDEOS_DESIGN + "byUpdatedData?reduce=false&limit=5"
BY_TYPE = VIDEOS_DESIGN + "byType?reduce=false"
COUCH_SERVER = couchdb.client.Server(BASE)
VID_DB = COUCH_SERVER['videos']

BASE_DIR = "/mnt/storage/mcandres/utorrent/xvideos/"

def infoLog(data):
    ts = time.time()
    st = datetime.datetime.fromtimestamp(ts).strftime('%Y-%m-%d %H:%M:%S')
    os.system("echo '[%s]%s'" % (st,data))

def queryDesignView( design_url ):
    retval = urllib2.urlopen(design_url).read()
    temp = json.loads(retval)
    return temp['rows']



def getDataInfo (doc_id, url):
    infoLog("[getDataInfo]")
    TEMP_DOC = VID_DB[doc_id]
    try:
        r = requests.get(url)
        data =  r.text
    except UnicodeEncodeError:
        VID_DB.delete(TEMP_DOC)
        return
  
    if (data == ''):
        return
    elif(data.find("deleted") > -1):
        infoLog("Video Deleted")
        TEMP_DOC['data_updated'] = 2
        VID_DB[doc_id] = TEMP_DOC
        return 
    
    res = re.findall ( 'flv_url=(.*?)&amp;url_bigthumb', data, re.DOTALL)
    flv_url = urllib.unquote(res[0]).decode('utf-8')
    TEMP_DOC['flv_url'] = flv_url
    infoLog( "flv_url = %s " % flv_url)
    res = re.findall ( 'url_bigthumb=(.*?)&amp;key', data, re.DOTALL)
    url_bigthumb = urllib.unquote(res[0]).decode('utf-8')
    TEMP_DOC['url_bigthumb'] = url_bigthumb
    infoLog( "url_bigthumb = %s" % url_bigthumb)
    tags = getTags(data)
    print "tags=",tags
    TEMP_DOC['tags'] = tags

    res = re.findall ( '<title>(.*?)</title>', data, re.DOTALL)
    title = res[0].replace('- XVIDEOS.COM','')
    infoLog( "title= %s" % title)
    TEMP_DOC['title'] = title
    TEMP_DOC['data_updated'] = 1

    VID_DB[doc_id] = TEMP_DOC

def getTags (data):
    res = re.findall ( 'a href="/tags/(.*?)">', data, re.DOTALL)
    tags = []
    for tag in res:
        if (tag != ''):
            tags.append(tag)
    return tags


def getVideosRelated (data):
    res = re.findall ( 'videoPageWriteRelated\(\[(.*?)\]\);</script>', data, re.DOTALL)
    json_string = "{ \"data\" : [[" + res[0] + "]]}"
    json_string = json_string.replace('id:','"id":')
    json_string = json_string.replace('u:','"u":')
    json_string = json_string.replace('i:','"i":')
    json_string = json_string.replace('d:','"d":')
    json_string = json_string.replace('t:','"t":')
    json_string = json_string.replace('r:','"r":')
    print json_string
    print json_string[2660:2670]
    print len(json_string)
    n = json.loads(json_string)

    print ">>>", n['data'][0][0][0]
    related = []
    for temp0 in n['data']:
       for temp in temp0:
           for temp2 in temp:
               print "xxx", temp2
               related.append(temp2)

    print "related len:", len(related)
    return related




def updateDataInfo ( data ):
    url = data['key']
    doc_id = data['id']
    infoLog("[updateDataInfo]url %s == %s" % (url, doc_id))
    getDataInfo (doc_id, url)



def retrieve_video ( data ):
    doc_id = data['id']
    infoLog("[retrieve_video] %s" % doc_id)
    TEMP_DOC = VID_DB[doc_id]
    video_dir = BASE_DIR + doc_id
    if (os.path.exists(video_dir)):
        infoLog("directory exists")
    else:
        try:
            os.mkdir(video_dir)
        except:
            infoLog("Error creating directory")
    
    try:
        infoLog("[retrieve_video] video will be saved at  %s" % video_dir)
        urllib.urlretrieve (TEMP_DOC['flv_url'], video_dir + "/video.flv")
        b = os.path.getsize(video_dir + "/video.flv")
        if ( b > 500 ):
            infoLog("[retrieve_video] video saved at  %s" % video_dir)
            TEMP_DOC['retrieved'] = 1
        else:
            infoLog("deleting directory")
            shutil.rmtree(video_dir)
            TEMP_DOC['retrieved'] = 3
            VID_DB[doc_id] = TEMP_DOC
            return
    except:
        infoLog("error retrieving video")
        TEMP_DOC['retrieved'] = 2
        infoLog("deleting directory")
        shutil.rmtree(video_dir)
        VID_DB[doc_id] = TEMP_DOC
        
        return
    try:
        urllib.urlretrieve (TEMP_DOC['url_bigthumb'], video_dir + "/thumb.jpg")
    except:
        infoLog("error retrieving thumbnail")

    json_string = json.dumps(TEMP_DOC,sort_keys=True, indent=4)
    f = open(video_dir + '/data.json', 'w')
    f.write(json_string)
    f.close()
    
    VID_DB[doc_id] = TEMP_DOC


def set_retrieve_zero ( data ):
    doc_id = data['id']
    TEMP_DOC = VID_DB[doc_id]
    TEMP_DOC['retrieved'] = 0
    VID_DB[doc_id] = TEMP_DOC
    



def retrieve_json ( data ):
    doc_id = data['id']
    TEMP_DOC = VID_DB[doc_id]
    video_dir = BASE_DIR + doc_id
    print os.path.exists(video_dir)
    if (os.path.exists(video_dir)):
        infoLog("directory exists")
    else:
        try:
            os.mkdir(video_dir)
        except:
            infoLog("Error creating directory")
        

    json_string = json.dumps(TEMP_DOC,sort_keys=True, indent=4)
    print "json_string" , json_string
    f = open(video_dir + '/data.json', 'w')
    f.write(json_string)
    f.close()
    




def main():
    data_list = queryDesignView( BY_DATA_NOT_UPDATED )
    for data in data_list:
        print data
        updateDataInfo ( data )
        retrieve_video ( data )
    #infoLog(BY_UPDATED_DATA)
    #data_list = queryDesignView( BY_UPDATED_DATA )
    #for data in data_list:
    #    infoLog("retrieve doc_id" + data['id'])
    #    infoLog("retrieve video" + data['key'])
    #    retrieve_video ( data )




if __name__ == "__main__":
    while(1):
        main()
        time.sleep(5)





