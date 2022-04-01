import requests
import json


def collect_cookies_from_request(url):
    response = requests.get(url)
    return response.cookies.get_dict()


url = "https://www.ups.com/track?loc=en&tracknum=1Z0333056837575011&requester=WT/trackdetails"
cookies = collect_cookies_from_request(url)
print(cookies)
print(json.dumps(cookies))
