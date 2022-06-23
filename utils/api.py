import time

from thefuzz import fuzz
from thefuzz import process

import requests
from bs4 import BeautifulSoup


class API:

    def uwuaas(self, text):
        url = 'https://uwuaas.herokuapp.com/api/'
        myobj = {'text': text}

        x = requests.post(url, json=myobj)

        return x.json()["text"]

    def vanmau(self, text):
        URL = "https://ditmenavi.xyz/"
        page = requests.get(URL)

        soup = BeautifulSoup(page.content, "html.parser")
        li = soup.find_all("li")
        max_rate = -1
        max_contents = ''
        max_titles = ''
        i = 0
        for group in li:
            title = group.find("h2")
            content = group.find("span")
            rate = fuzz.ratio(text, title.text)
            if rate > max_rate:
                max_rate = rate
                max_contents = content.text
                max_titles = title.text
            i += 1

        return max_contents

    def ggmeet(self):

        URL = " http://meet.google.com/new"
        page = requests.get(URL)

        time.sleep(5)
        return page.url
