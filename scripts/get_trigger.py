import json
import sys

triggerfile = open(sys.argv[1])
trigger = json.load(triggerfile)

if len(sys.argv) == 3:
    print(trigger[sys.argv[2]])
if len(sys.argv) == 4:
    print(trigger[sys.argv[2]][sys.argv[3]])
