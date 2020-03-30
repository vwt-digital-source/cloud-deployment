import sys

with open(sys.argv[1]) as f:
    one = f.readlines()

with open(sys.argv[2]) as f:
    two = f.readlines()

result = [item for item in one if item not in two]

for item in result:
    print(item)
