import sys
from main import publish_build_result_func


class Context:
    def __init__(self):
        self.properties = {}

context = Context()
msg = {"data": "data"}
print(publish_build_result_func(msg, context))
