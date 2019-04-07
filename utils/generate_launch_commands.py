#!/usr/bin/env python

__author__ = "Damian Kelly"

# import argparse
import requests
import json
import os

print("\nThis script discovers your Philips Hue IP address, generates an API key and provides example commands to run "
      "the functionality either in the command line, in Docker or on a Kubernetes cluster.\n")

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
    print("Error running script: \n'{}'\nPress the link button before running this script."
          .format(resp_json_dict[0]["error"]["description"]))
    exit()

# TODO: for debugging:
# resp_json_dict = json.loads("""[{"success": {"username": "debug_API_key"}}] """)

api_key = resp_json_dict[0]["success"]["username"]

padding = "="*70
print("{}\nInstructions to run in the command line\n{}".format(padding, padding))

os.chdir('..')
root_path = os.getcwd()
path_to_server = os.path.join(os.getcwd(), 'server')
path_to_get_data = os.path.join(os.getcwd(), 'get_data')

instructions = """To run directly on a PC in the command line, you must have the
data polling script AND the server script running at the same time.

To poll the data, open a terminal window and run the commands:

cd <path_to_get_data>
export HUE_IP_ADDRESS="<ip>"
export HUE_API_KEY="<api_key>"
python hue_polling_to_db.py

To run the server, open a terminal window and run the commands

cd <path_to_server>
python api.py

Then you can point your browser at:
http://localhost:5000/index.html"""

instructions = instructions.replace("<path_to_get_data>", path_to_get_data)\
    .replace("<ip>", hub_ip_address)\
    .replace("<api_key>", api_key)\
    .replace("<path_to_server>", path_to_server)

print(instructions)

print("{}\nInstructions to run in a Docker container\n{}".format(padding, padding))

instructions = """To build a docker container yourself and run use the following commands:

cd <root_path>
docker build -t damok6/apartment-monitor:1.0 .
docker run -t -p 5000:5000 -e HUE_IP_ADDRESS="<ip>" -e HUE_API_KEY="<api_key>" damok6/apartment-monitor:1.0

However, if you do not wish to build your own container and simply use the version stored in the docker registry, use the following command:

docker run -t -p 5000:5000 -e HUE_IP_ADDRESS="<ip>" -e HUE_API_KEY="<api_key>" damok6/apartment-monitor:1.0

Finally use 'docker ps' to confirm the container is running.

Then you can point your browser at:
http://localhost:5000/index.html"""

instructions = instructions.replace("<root_path>", root_path)\
    .replace("<ip>", hub_ip_address)\
    .replace("<api_key>", api_key)

print(instructions)

yaml = """apiVersion: apps/v1
kind: Deployment
metadata:
  name: apartmentmonitor
  labels:
    app: apartmentmonitor
  annotations:
    monitoring: "true"
spec:
  replicas: 1
  selector:
    matchLabels:
      app: apartmentmonitor
  template:
    metadata:
      labels:
        app: apartmentmonitor
    spec:
      containers:
      - image: damok6/apartment-monitor:1.0
        name: apartment-monitor
        ports:
        - containerPort: 5000
        env:
        - name: HUE_IP_ADDRESS
          value: "<ip>"
        - name: HUE_API_KEY
          value: "<api_key>"
---
apiVersion: v1
kind: Service
metadata:
  labels:
    app: apartmentmonitor
  name: apartmentmonitor
spec:
  externalIPs:
  - <kube_external_ip>
  ports:
  - nodePort: 32500
    port: 5000
    protocol: TCP
    targetPort: 5000
  selector:
    app: apartmentmonitor
  type: LoadBalancer
"""

kube_file = "apartment_monitor.yaml"
with open(kube_file, "w") as f:
    f.write(yaml.replace("<ip>", hub_ip_address).replace("<api_key>", api_key))

print("{}\nInstructions to launch on a Kubernetes cluster\n{}".format(padding, padding))

instructions = """This script also automatically generates a yaml file which can be applied to a Kubernetes cluster.

When run using kubectl this yaml will create a Kubernetes deployment and a Kubernetes service which exposes the web server port on the specified Kubernetes node.

The yaml is created in the location:
<kube_file>

You must go into the file and modify the <kube_external_ip> setting to match the IP address for the Kubernetes node on which you wish to expose your service.

Then you can deploy this application on Kubernetes using the command:

kubectl apply -f <kube_file>

When deployed, you can point your browser at:
http://<kube_external_ip>:32500/index.html"""


instructions = instructions.replace("<kube_file>", os.path.join(root_path, kube_file))

print(instructions)
print(padding)

