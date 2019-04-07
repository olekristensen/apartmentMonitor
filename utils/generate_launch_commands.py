#!/usr/bin/env python

__author__ = "Damian Kelly"

# import argparse
import requests
import json
import os

# parser = argparse.ArgumentParser(description='Calculate the API key and generate some sample commands for starting '
#                                              'the logging code or deploying the code to Docker or Kubernetes.')
# parser.add_argument('integers', metavar='N', type=int, nargs='+',
#                    help='an integer for the accumulator')
# args = parser.parse_args()

resp = requests.get("https://www.meethue.com/api/nupnp")
resp_json_dict = json.loads(resp.text)

if len(resp_json_dict) > 1:
    raise Exception('This code is only meant for homes with one Hue device.')

hub_ip_address = resp_json_dict[0]['internalipaddress']

resp = requests.post("http://{}/api".format(hub_ip_address), '{"devicetype":"my_hue_app#apartment_monitor"}')
resp_json_dict = json.loads(resp.text)

if "error" in resp_json_dict[0]:
    print("Error running script: \n{}\nPress the link button before running this script."
          .format(resp_json_dict[0]["error"]["description"]))
    exit()

# # TODO: for debugging:
# resp_json_dict = json.loads("""[{"success": {"username": "debug_API_key"}}] """)

api_key = resp_json_dict[0]["success"]["username"]

padding = "="*50
print("{}\nInstructions to run on PC\n{}".format(padding, padding))

os.chdir('..')
path_to_server = os.path.join(os.getcwd(), 'server')
path_to_get_data = os.path.join(os.getcwd(), 'get_data')

instructions = """To run directly on a PC, you must have the data polling
script AND the server script running at the same time.
To poll the data, open a terminal window and run the commands:

cd <path_to_get_data>
export HUE_IP_ADDRESS="<ip>"
export HUE_API_KEY="<api_key>"
python hue_polling_to_db.py

To run the server, open a terminal window and run the commands

cd <path_to_server>
python api.py
"""

instructions = instructions.replace("<path_to_get_data>", path_to_get_data)\
    .replace("<ip>", hub_ip_address)\
    .replace("<api_key>", api_key)\
    .replace("<path_to_server>", path_to_server)

print(instructions)


# print("{},{}".format(hub_ip_address, api_key))



