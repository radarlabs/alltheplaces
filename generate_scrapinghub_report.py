#!/usr/bin/env python3

import os
import sys

from scrapinghub import ScrapinghubClient
from locations.exporters import GeoJsonExporter

import logging
import boto3
from botocore.exceptions import ClientError
import json
from io import BytesIO


import zipfile

zf = zipfile.ZipFile('alltheplaces.zip', 
                     mode='w',
                     compression=zipfile.ZIP_DEFLATED, 
                     )
BUCKET_NAME = 'com.radar.public.alltheplaces'                     

apiKey = os.environ['SCRAPINGHUB_APIKEY']
if not apiKey:
  print('missing env variable in SCRAPINGHUB_APIKEY')
  sys.exit(1)
client = ScrapinghubClient(apiKey)

def get_s3():
  return boto3.resource(
    's3',
    region_name='us-east-1',
    aws_access_key_id=os.environ['AWS_ACCESS_KEY_ID'],
    aws_secret_access_key=os.environ['AWS_SECRET_ACCESS_KEY']
  )

def upload_data(filename, content, mimeType):
  s3 = get_s3()
  obj = s3.Object(BUCKET_NAME, filename)
  bytesIO = BytesIO()
  bytesIO.write(content.encode('utf-8'))
  bytesIO.seek(0)
  obj.put(Body=bytesIO, ACL='public-read', ContentType=mimeType)

def upload_json(filename, content):
  upload_data(
    filename,
    json.dumps(content),
    'application/json'
  )


def upload_file(filename, to_filename):
  get_s3().meta.client.upload_file(filename, BUCKET_NAME, to_filename, ExtraArgs={'ACL':'public-read'})

def main():
  projectId = client.projects.list()[0]
  project = client.get_project(projectId)

  spiderLatestMetadatas = {}
  for spiderDict in project.spiders.list():
    spiderId = spiderDict['id']
    spider = project.spiders.get(spiderId)
    print(spiderId)
    metadata = getSpiderMetadata(spider)
    if len(metadata) > 0:
      spiderLatestMetadatas[spiderId] = {
        'status': 'ran',
        'metadata': metadata[0]
      }
    else:
      spiderLatestMetadatas[spiderId] = {
        'status': 'never_run',
        'metadata': {}
      }

    upload_json('%s/metadata.json' % spiderId, {'metadata': metadata})

    latestJob = getLatestJobForSpider(spider)
    if latestJob:
      featureCollection = makeFeatureCollectionFromItem(latestJob.items.iter())
      upload_json('%s/latest-places.geojson' % spiderId, featureCollection)
      upload_json('%s/%s.geojson' % (spiderId, latestJob.key), featureCollection)
      zf.writestr('alltheplaces/%s.geojson' % spiderId, json.dumps(featureCollection))

    # print(featureCollection)

  upload_json('latest-metadata.json', {'spiders': spiderLatestMetadatas})
  zf.close()
  upload_file('alltheplaces.zip', 'alltheplaces.zip',)
  

def getJobMetadataFromKey(jobKey):
  # dict_keys(['_shub_worker', 'api_url', 'deploy_id', 'priority', 'tags', 'units', 'spider_type', 'completed_by', 'scrapystats', 'spider', 'close_reason', 'finished_time', 'started_by', 'scheduled_by', 'version', 'project', 'running_time', 'pending_time', 'state'])
  job = client.get_job(jobKey)
  return dict([p for p in job.metadata.iter()])

def getLatestJobForSpider(spider):
  jobs = [j for j in spider.jobs.iter()]
  if len(jobs) == 0:
    return None
  return client.get_job(jobs[0]['key'])

def getSpiderMetadata(spider):
  spiderJobMetadatas = [
    getJobMetadataFromKey(s['key']) for s in spider.jobs.iter()
  ]

  return spiderJobMetadatas


def makeFeatureFromItem(item):
  exporter = GeoJsonExporter(None)
  partialGeoJsonRecord = exporter._get_serialized_fields(item)
  geoJsonRecord = {}
  for (key, value) in partialGeoJsonRecord:
    geoJsonRecord[key] = value
  return geoJsonRecord

def makeFeatureCollectionFromItem(items):
  return {"type":"FeatureCollection","features":[makeFeatureFromItem(i) for i in items]}


if __name__ == "__main__":
  main()