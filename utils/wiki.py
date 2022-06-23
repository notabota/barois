import wikipedia


class API:

    def summary(self, text):
        print(wikipedia.summary(text))
