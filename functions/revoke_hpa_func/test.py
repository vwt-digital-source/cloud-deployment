from main import revoke_HPA


class Context:
    def __init__(self):
        self.properties = {}


context = Context()
msg = {"data": "data"}
print(revoke_HPA(msg, context))
