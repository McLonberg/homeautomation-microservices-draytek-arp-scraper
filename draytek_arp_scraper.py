# Original Code snippets were from https://gist.github.com/doobeh/942faf81e0958cc973b7


from config import *
# You can overwrite things like HOST here if you want to ensure you don't store your details in a public repo.
from secrets import *
import re
import requests
import urllib.request
import base64
import string
import random
import csv
import json
import paho.mqtt.client as mqtt
import time
from bs4 import BeautifulSoup

# Variables
devices = []
tracked_devices = []
active_devices = []
inactive_devices = []
ENCODE_LOGIN = True
active_device_count = 0

# Draytek router requires an sFrmAuthString which is consistent through the session
# This string is randomly generated in current firmware so a generator function will work.  For now.


def id_generator(size=15):
    """Generate a random string of fixed length """
    lettersAndDigits = string.ascii_letters + string.digits
    return ''.join(random.choice(lettersAndDigits) for i in range(15))


def encode_login(ba):
    return base64.b64encode(ba.encode()).decode('ascii')


MyFormAuth = id_generator()


username = encode_login(USERNAME)
password = encode_login(PASSWORD)


cookie_url_form_data = {"aa": username, "ab": password, "sslgroup": "-1",
                        "obj4": "", "obj5": "", "obj6": "", "obj7": "", "obj3": "", "sFormAuthStr": MyFormAuth}

cookie_headers = {
    "POST": "/cgi-bin/wlogin.cgi HTTP/1.1",
    "Host": HOST,
    "Connection": "keep-alive",
    "Content-Length": "102",
    "Cache-Control": "no-cache",
    "Origin": "https://"+HOST,
    "Upgrade-Insecure-Requests": "1",
    "DNT": "1",
    "Content-Type": "application/x-www-form-urlencoded",
    "User-Agent": "Mozilla/5.0",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9",
    "Referer": "https://"+HOST+"/weblogin.htm",
    "Referrer-Policy": "strict-origin-when-cross-origin",
    "Accept-Encoding": "gzip, deflate",
    "Accept-Language": "en-GB,en;q=0.9,en-US;q=0.8,da;q=0.7,nb;q=0.6,no;q=0.5",
    "sec-fetch-dest": "document",
    "sec-fetch-mode": "navigate",
    "sec-fetch-site": "same-origin"
}

#cookie_url = 'https://'+HOST+'/cgi-bin/wlogin.cgi'
cookie_url = 'http://'+HOST+'/cgi-bin/wlogin.cgi'

# ARP TAble EXtraction
#refresh_url = 'https://{host}/cgi-bin/arp.cgi?sFormAuthStr={auth}'.format(
#    host=HOST,
#    auth=MyFormAuth
#)

refresh_url = 'http://{host}/cgi-bin/arp.cgi?sFormAuthStr={auth}'.format(
    host=HOST,
    auth=MyFormAuth
)


#query_url = 'https://{host}/doc/iparptbl.sht'.format(host=HOST) # ARP Table
query_url = 'http://{host}/doc/iparptbl.sht'.format(host=HOST) # ARP Table


#refresh_url = 'https://{host}/cgi-bin/V2X00.cgi?sFormAuthStr={auth}&fid=2096'.format(
#    host=HOST,
#    auth=MyFormAuth
#)

#query_url = 'https://{host}//doc/digdatam.htm'.format(host=HOST)  # DataFlow Monitor TAble




# Make the requests for data:
# 1. Get a cookie
# 2. Ask router to refresh the ARP cache
# 3. Get the ARP output

session = requests.Session()

initial_response = session.post(
    cookie_url, headers=cookie_headers, data=cookie_url_form_data, allow_redirects=False, timeout=10
)

# initial_response = session.post(
#    cookie_url, headers=cookie_headers, data=cookie_url_form_data)
# initial_response = session.get(cookie_url),

# Beautiful Soup attempt
#soup = BeautifulSoup(initial_response.content, 'html.parser')
#print(initial_response.status_code)
# print(soup)


# exit()
# print(initial_response.text)
#print(initial_response.headers)
#print(initial_response.cookies)
# print(initial_response.is_redirect)
# print(initial_response.content)
# print(initial_response.history)
#print(len(initial_response.cookies))
# print(initial_response.is_permanent_redirect)

#session.close()


#exit()


refresh = session.get(refresh_url)


results = session.get(query_url).text
#print(results)


#exit()

# Parse the results for device information and turn in to a list
regex = r"var lines=(\[([^]]+)\])"
parsed = re.search(regex, results)
#print(parsed)
#exit()

if not parsed:
    print("Nowt found...  Either authentication failed or the arp cache is empty.  The latter would NEVER happen in my house so chances are it is your authentication...")
    quit()

data = eval('[' + parsed[2] + ']')
length = len(data)

# Loop through and create our list

for x in range(length):
    if x == 0:
        continue  # Ignore header line
    if len(data[x]) == 0:
        continue  # Ignore empty entries.  There are 512 entries in list regardless of no. of active ARP cache entries
    output = data[x]
    # Split output.  Someone with better REGEX skills than me could probably improve this.
    # However, each line from ARP cache is 86 characters long regardless so the slicing works.
    ip = output[:15].strip()
    mac = output[16:35].strip()
    host = output[36:63].strip()
    if len(host) == 0:
        host = "-"  # Not every entry in arp cache has a host name
    devices.append((ip, mac, host))

#print(devices)
#exit()

# CSV
if FileFormat == 'CSV':
    with open("tracked_devices.csv") as f:
        readCSV = csv.reader(f, delimiter=",")
        for row in readCSV:
            tracked_devices.append(row[0])
        f.close()
else:
    # JSON
    if FileFormat == 'JSON':
        with open("tracked_devices.json") as f:
            readJSON = json.load(f)
            for entry in readJSON['tracked_devices']:
                dev = str(entry['device'])
                if any(dev in s for s in devices):
                    device_status = 'Home'
                    active_device_count += 1
                else:
                    device_status = 'Away'
                tracked_devices.append(
                    [entry['device'], entry['name'], device_status])
            f.close

print(tracked_devices)
curtime = time.strftime("%d/%m/%Y %H:%M:%S", time.localtime())
print(curtime)

if active_device_count == 0:
    print("Draytek ARP Scraper:",
          "No tracked devices currently active. No-One at home")
else:
    print("Draytek ARP Scraper:", active_device_count, "device(s) active.")


# MQTT
if network == 'remote':
    BROKER = REMOTE_BROKER

# MQTT Callback functions


def on_connect(client, userdata, flags, rc):
    print("CONNACK received with code %d." % (rc))


client = mqtt.Client("ARP_1")
client.on_connect = on_connect
client.connect(BROKER)
time.sleep(4)

client.loop_start()  # Start loop
for track in tracked_devices:
    topic = BROKER_TOPIC+track[1]
    client.publish(topic, track[2])
    print(topic, track[2])
client.loop_stop()
