import sys

# Base list
with open(sys.argv[1]) as f:
    one = f.readlines()

# Compare list
with open(sys.argv[2]) as f:
    two = f.readlines()

# Exclude list
with open(sys.argv[3]) as f:
    three = f.readlines()

result = [item for item in one if item not in two]

for item in list(set(result)):
    if item not in three:
        print(item)
