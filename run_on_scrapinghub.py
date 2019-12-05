#!/usr/bin/env python3

import os
import sys

from scrapinghub import ScrapinghubClient
from locations.exporters import GeoJsonExporter

import logging
import boto3
from botocore.exceptions import ClientError
import json

apiKey = os.environ['SCRAPINGHUB_APIKEY']
if not apiKey:
  print('missing env variable in SCRAPINGHUB_APIKEY')
  sys.exit(1)
client = ScrapinghubClient(apiKey)

def upload_data(filename, content):
  s3 = boto3.resource(
    's3',
    region_name='us-east-1',
    aws_access_key_id=os.environ['AWS_ACCESS_KEY_ID'],
    aws_secret_access_key=os.environ['AWS_SECRET_ACCESS_KEY']
  )
  s3.Object('com.radar.public.alltheplaces', filename).put(Body=content)  


def main():
  projectId = client.projects.list()[0]
  project = client.get_project(projectId)

  spiderLatestMetadatas = {}
  for spiderDict in project.spiders.list()[0:1]:
    spiderId = spiderDict['id']
    spider = project.spiders.get(spiderId)
    print(spiderId)
    metadata = getSpiderMetadata(spider)
    spiderLatestMetadatas[spiderId] = metadata[0:1]
    upload_data('%s/metadata.json' % spiderId, metadata)

    latestJob = getLatestJobForSpider(spider)
    featureCollection = makeFeatureCollectionFromItem(latestJob.items.iter())
    upload_data('%s/latest-places.geojson' % spiderId, json.dumps(featureCollection))
    upload_data('%s/%s.geojson' % (spiderId, latestJob.key), json.dumps(featureCollection))

    # print(featureCollection)

  upload_data('latest-metadata.json', json.dumps({'spiders': spiderLatestMetadatas}))
  

def getJobMetadataFromKey(jobKey):
  # dict_keys(['_shub_worker', 'api_url', 'deploy_id', 'priority', 'tags', 'units', 'spider_type', 'completed_by', 'scrapystats', 'spider', 'close_reason', 'finished_time', 'started_by', 'scheduled_by', 'version', 'project', 'running_time', 'pending_time', 'state'])
  job = client.get_job(jobKey)
  return dict([p for p in job.metadata.iter()])

def getLatestJobForSpider(spider):
  return client.get_job(next(spider.jobs.iter())['key'])

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