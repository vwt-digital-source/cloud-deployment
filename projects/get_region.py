import json
import sys

DEFAULT_REGION = 'europe-west'

file = open(sys.argv[1])
project = json.load(file)

print(project.get('appEngineRegion', DEFAULT_REGION))
