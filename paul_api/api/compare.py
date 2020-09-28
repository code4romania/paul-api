import requests
from pprint import pprint

url = 'https://prezenta.roaep.ro/locale27092020/data/json/sicpv/pv/pv_tm_part.json'

r = requests.get(url)
pprint(r)