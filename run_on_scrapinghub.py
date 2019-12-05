#!/usr/bin/env python3

import os
import sys

from scrapinghub import ScrapinghubClient

apiKey = os.environ['SCRAPINGHUB_APIKEY']
if not apiKey:
  print('missing env variable in SCRAPINGHUB_APIKEY')
  sys.exit(1)
client = ScrapinghubClient(apiKey)

projectId = client.projects.list()[0]
project = client.get_project(projectId)

for (spiderDict, index) in enumerate(project.spiders.list()):
  print(f'kicking off {spiderDict['id']} - {index}')
  job = project.jobs.run(spiderDict['id'])