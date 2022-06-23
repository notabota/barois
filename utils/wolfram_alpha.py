import wolframalpha


class WolframAlpha:

    def __init__(self, app_id):
        self.client = wolframalpha.Client(app_id)

    def query(self, search_query):
        return self.client.query(search_query)
