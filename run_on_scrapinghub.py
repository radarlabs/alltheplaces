#!/usr/bin/env python3

import os
import sys
import traceback
import time

import scrapinghub
from scrapinghub import ScrapinghubClient

apiKey = os.environ['SCRAPINGHUB_APIKEY']
if not apiKey:
  print('missing env variable in SCRAPINGHUB_APIKEY')
  sys.exit(1)
client = ScrapinghubClient(apiKey)

projectId = client.projects.list()[0]
project = client.get_project(projectId)

for (index, spiderDict) in enumerate(project.spiders.list()):
  print(f'kicking off {spiderDict["id"]} - {index}')
  numTries = 1
  ranSuccessfully = False
  while numTries < 6 and not ranSuccessfully:
    try:
      job = project.jobs.run(spiderDict['id'])
      ranSuccessfully = True
    except scrapinghub.client.exceptions.DuplicateJobError:
      print('--> already in queue')
      ranSuccessfully = True
    except:
      numTries+=1
      print('--> failed, sleeping 10s then going for try %s' % numTries)
      traceback.print_exc(file=sys.stdout)
      time.sleep(10)
      

