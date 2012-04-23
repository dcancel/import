#!/usr/bin/env python

# import os for file system functions
import os
# import json
import json
# shutil for file renaming
import shutil
import sys
import time

# import flickrapi
# `easy_install flickrapi` or `pip install flickrapi`
from openphoto import OpenPhoto

from os.path import join, getsize

# _decode_list() and _decode_data() adds support for Unicode strings in Flickr photo titles and descriptions.
# These functions came from this post: http://stackoverflow.com/a/6633651/1232882
def _decode_list(data):
    rv = []
    for item in data:
        if isinstance(item, unicode):
            item = item.encode('utf-8')
        elif isinstance(item, list):
            item = _decode_list(item)
        elif isinstance(item, dict):
            item = _decode_dict(item)
        rv.append(item)
    return rv

def _decode_dict(data):
    rv = {}
    for key, value in data.iteritems():
        if isinstance(key, unicode):
           key = key.encode('utf-8')
        if isinstance(value, unicode):
           value = value.encode('utf-8')
        elif isinstance(value, list):
           value = _decode_list(value)
        elif isinstance(value, dict):
           value = _decode_dict(value)
        rv[key] = v

# main program
def import_into_openphoto(client):


  for root, dirs, files in os.walk('fetched/'):
    total = len(files)
    current = 1
    processed = 0
    errored = 0
    start_time = time.time()
    print "Found a total of %d files to process" % total
    for i in files:
      print "Processing %d of %d %s ..." % (current, total, i),
      sys.stdout.flush()
      current = current + 1
      infile = "fetched/%s" % i
      f = open(infile, 'r')
      json_str = f.read()
      f.close()

      shutil.move(infile, "errored/%s" % i)

      params = json.loads(json_str, object_hook=_decode_dict)
      resp = client.post('/photo/upload.json', params)
      result = json.loads(resp)
      if result['code'] == 201:
        print "OK"
        processed = processed + 1
        shutil.move("errored/%s" % i, "processed/%s" % i)
      else:
        code = result['code']
        message = result['message']
        print "FAILED: %d - %s" % (code, message)
        if code == 409 :
          shutil.move("errored/%s" % i, "duplicates/%s" % i)
        else:
          print params
        errored = errored + 1
      sys.stdout.flush()

    end_time = time.time()
    total_time = (end_time - start_time) / 60.0
    photos_minute = int(total / total_time)

    if total > 0:
      print "Results. Processed: %d. Errored: %d." % (processed, errored)
      print "Imported %d photos at %d photos/minute." % (total, photos_minute)
  
# create a directory only if it doesn't already exist
def createDirectorySafe( name ):
  if not os.path.exists(name):
    os.makedirs(name)


if __name__ == '__main__':
  import argparse

  parser = argparse.ArgumentParser(description='Import photos into an OpenPhoto instance')
  parser.add_argument('--host', required=True)
  parser.add_argument('--consumer-key', required=True)
  parser.add_argument('--consumer-secret', required=True)
  parser.add_argument('--token', required=True)
  parser.add_argument('--token-secret', required=True)
  config = parser.parse_args()

  client = OpenPhoto(config.host, config.consumer_key, config.consumer_secret, config.token, config.token_secret)

  # check if a processed and errored directories exist else create them
  createDirectorySafe('processed')
  createDirectorySafe('errored')
  createDirectorySafe('duplicates')

  import_into_openphoto(client)
