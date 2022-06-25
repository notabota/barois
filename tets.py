from pprint import pprint

import bs4
import requests
from org_fbchat import _util


def is_home(url):
    parts = _util.urlparse(url)
    # Check the urls `/home.php` and `/`
    return "home" in parts.path or "/" == parts.path


def session_factory(user_agent=None):
    session = requests.Session()
    # session.headers["Referer"] = "https://www.facebook.com"
    # session.headers["Accept"] = "text/html"

    # TODO: Deprecate setting the user agent manually
    # session.headers["User-Agent"] = user_agent
    print(session.headers)
    print(session.cookies)
    return session


def find_input_fields(html):
    # return bs4.BeautifulSoup(html, "html.parser", parse_only=bs4.SoupStrainer("input"))
    return bs4.BeautifulSoup(html, "html.parser")


session = session_factory(
    user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/102.0.5005.124 Safari/537.36 Edg/102.0.1245.44")

soup = find_input_fields(session.get("https://m.facebook.com/login").text)

print(soup.contents)

soup = soup.find_all("input")

data = dict(
    (elem["name"], elem["value"])
    for elem in soup
    if elem.has_attr("value") and elem.has_attr("name")
)

data["email"] = "basicallyarois@gmail.com"
data["pass"] = "B4rois"
data["login"] = "Log In"

pprint(data)
pprint(session.headers)
pprint(session.cookies)

r = session.post("https://m.facebook.com/login/", data=data)

print(r.status_code)
print(r.url)
print(r.content)

# # Usually, 'Checkpoint' will refer to 2FA
# if "checkpoint" in r.url and ('id="approvals_code"' in r.text.lower()):
#     code = on_2fa_callback()
#     r = _2fa_helper(session, code, r)

# Sometimes Facebook tries to show the user a "Save Device" dialog
if "save-device" in r.url:
    r = session.get("https://m.facebook.com/login/save-device/cancel/")

# Sometimes facebook redirects to facebook.com/cookie/consent-page/*[...more directories]. So, go to homepage
if "cookie" in r.url:
    r = session.get("https://m.facebook.com/", allow_redirects=False)

print(r.url)
print(is_home(r.url))
