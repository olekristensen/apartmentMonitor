import time
import json
import sys
import os
import csv
import urllib2
import sqlite3

csv.field_size_limit(sys.maxsize)

if "HUE_IP_ADDRESS" in os.environ:
	HUE_IP_ADDRESS = os.environ["HUE_IP_ADDRESS"]
else:
	HUE_IP_ADDRESS = "set_ip_address_here"  # If you don't want to set in environment variables

if "HUE_API_KEY" in os.environ:
	HUE_API_KEY = os.environ["HUE_API_KEY"]
else:
	HUE_API_KEY = "set_key_here"  # If you don't want to set in environment variables

DB = "../hue_data.db"
DB_TABLE = "hue_results"
DB_TABLE_KNMI_CACHE = "knmi_cache"
OUT_FILE  = "../hue_results.csv"
HUE_API_LOCATION = "http://{}/api/".format(HUE_IP_ADDRESS)

INTERVAL = 10 #seconds between polls
WRITE_FILE = False

print("Polling API Location: {}".format(HUE_API_LOCATION))

def initialize_db():
	""" When not available, creates Database and table.
	Otherwise, does nothing.
	"""
	# Set up DB connection
	con = sqlite3.connect(DB)
	cur = con.cursor()
	
	# Create table (if not exists)
	try:
		cur.execute("""
			CREATE TABLE {0} (
				un UNIQUE,
				polling_timestamp,
				device_name,
				device_type,
				device_modelid,
				device_manufacturer,
				device_swversion,
				device_uid,
				value,
				value_timestamp
			);
		""".format(DB_TABLE))
	except:
		pass

	# Create table (if not exists)
	try:
		cur.execute("""
			CREATE TABLE {0} (
				polling_timestamp
			);
		""".format(DB_TABLE_KNMI_CACHE))
	except:
		pass

	con.close()

def write_db(results):
	""" Writes list of CSV lines (results) to database
	"""
	# Set up DB connection
	con = sqlite3.connect(DB)
	cur = con.cursor()

	time_string = time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime())

	# Write to DB
	for line in results:
		print(line)
		try:
			split_line = line.split(';')
			un = "{0}{1}".format(split_line[0],split_line[7])
			insert_data = ','.join(split_line)
			#un = "{0}{1}".format(insert_data[0],insert_data[7])
			insert_vals = "{},{},{}".format(un, time_string, insert_data)
			insert_vals = ','.join(["'{}'".format(val) for val in insert_vals.split(',')])
			print(un)
			print(insert_vals)
			query_str = "INSERT OR IGNORE INTO {0} VALUES({1})".format(DB_TABLE, insert_vals)
			print(query_str)
			cur.execute(query_str)
		except:
			print "WARNING: Failed writing line to DB; '{0}'".format(line)
	con.commit()
	con.close()

def retrieve_data(request_string):
	""" Question Hue API with request_string
	"""
	try:
		#print("{0}{1}/{2}".format(HUE_API_LOCATION, HUE_API_KEY, request_string))
		result = urllib2.urlopen("{0}{1}/{2}".format(HUE_API_LOCATION, HUE_API_KEY, request_string)).read()
		result_json = json.loads(result)
		return result_json
	except:
		print "Network unreachable. Retrying on next iteration..." 
		return {}

def write_file(file, lines):
	""" Write given lines to given file
	"""
	time_string = time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime())
	for line in lines:
		try:
			with open(file, "a") as f:
			    f.write("{0};{1}\n".format(time_string,line))
			#print line
		except:
			print "WARNING: Failed writing line to file; '{0}'".format(line)


def retrieve_knmi_weather_parent():
	""" Parent of KNMI polling to make sure only once every 5 minutes is being polled.
	In any other situation we will use the last known value
	"""
	# Check if last KNMI poll < 5 minutes old. Don't retrieve new value.
	con = sqlite3.connect(DB)
	cur = con.cursor()

	query = """
			SELECT 
				MAX(polling_timestamp)
				FROM {0};
		""".format(DB_TABLE_KNMI_CACHE)

	# Execute query
	cur.execute(query)        	
	rows = cur.fetchall()

	# Parse age
	latest_time = "1970-01-01 01:00:00"
	for row in rows:
		latest_time = row[0]
	print(latest_time)
	if latest_time is None:
		return retrieve_knmi_weather()

	
	if time.strptime(latest_time, "%Y-%m-%d %H:%M:%S") > (time.gmtime()-900):
		# Save new latest
		try:
			time_string = time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime())
			cur.execute("INSERT OR IGNORE INTO {0} VALUES({1})".format(DB_TABLE_KNMI_CACHE, time_string))
		except:
			print "WARNING: Failed writing time to KNMI DB Cache; '{0}'"

		# Retrieve
		return retrieve_knmi_weather()
	else:
		return False

	con.close()

def retrieve_knmi_weather():
	""" Retrieve current weather in Voorschoten from KNMI website
	"""	
	results = []
	try:
		# retrieve KNMI HTML
		url = "http://www.knmi.nl/nederland-nu/weer/waarnemingen"
		response = urllib2.urlopen(url)
		html = response.read()

		# Cut out part containing the info we need
		part = html.split("<td class="">Voorschoten</td>")[1]
		part = part.split("</tr>")[0]
		parts = part.split("<td class=\"\">")
		rotterdam_temperature = parts[1].replace("</td>","")
		rotterdam_humidity = parts[2].replace("</td>","")
		rotterdam_wind_speed = parts[4].replace("</td>","")
		rotterdam_wind_direction = parts[3].replace("</td>","")
		rotterdam_visibility = parts[5].replace("</td>","")
		rotterdam_air_pressure = parts[6].replace("</td>","")

		# Add results in correct format
		time_string = time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime())
		results.append("{0};{1};{2};{3};{4};{5};{6};{7}".format(
				"KNMI_ROTTERDAM_TEMPERATURE",
				"Temperature",
				"None",
				"KNMI",
				"1.0",
				"KNMI_RDAM_T_0",
				rotterdam_temperature,
				time_string
			))
		results.append("{0};{1};{2};{3};{4};{5};{6};{7}".format(
				"KNMI_ROTTERDAM_HUMIDITY",
				"Humidity",
				"None",
				"KNMI",
				"1.0",
				"KNMI_RDAM_H_0",
				rotterdam_humidity,
				time_string
			))
		results.append("{0};{1};{2};{3};{4};{5};{6};{7}".format(
				"KNMI_ROTTERDAM_WIND_SPEED",
				"Wind speed (m/s)",
				"None",
				"KNMI",
				"1.0",
				"KNMI_RDAM_WS_0",
				rotterdam_wind_speed,
				time_string
			))
		results.append("{0};{1};{2};{3};{4};{5};{6};{7}".format(
				"KNMI_ROTTERDAM_WIND_DIRECTION",
				"Wind direction",
				"None",
				"KNMI",
				"1.0",
				"KNMI_RDAM_WD_0",
				rotterdam_wind_direction,
				time_string
			))
		results.append("{0};{1};{2};{3};{4};{5};{6};{7}".format(
				"KNMI_ROTTERDAM_VISIBILITY",
				"Visibility (m)",
				"None",
				"KNMI",
				"1.0",
				"KNMI_RDAM_V_0",
				rotterdam_visibility,
				time_string
			))
		results.append("{0};{1};{2};{3};{4};{5};{6};{7}".format(
				"KNMI_ROTTERDAM_PRESSURE",
				"Air pressure (hPa)",
				"None",
				"KNMI",
				"1.0",
				"KNMI_RDAM_P_0",
				rotterdam_air_pressure,
				time_string
			))
	except:
		print "Failed retrieving KNMI data"

	return results

def parse_results(result):
	""" Parse results from Hue API into one CSV line per Hue measurement.
	Returns list of CSV lines
	"""
	results_parsed = []
	for device in result:
		try:
			current = result[device]

			device_data = "{0};{1};{2};{3};{4};{5}".format(
				current["name"],
				current["type"],
				current["modelid"],
				current["manufacturername"],
				current["swversion"],
				current["uniqueid"])

			device_specific = ";"
			if current["type"] == "Daylight":
				device_specific = "{0};{1}".format(
					current["state"]["daylight"],
					current["state"]["lastupdated"].replace("T"," "))
			if current["type"] == "ZLLTemperature":
				device_specific = "{0};{1}".format(
					current["state"]["temperature"],
					current["state"]["lastupdated"].replace("T"," "))
			if current["type"] == "ZLLPresence":
				device_specific = "{0};{1}".format(
					current["state"]["presence"],
					current["state"]["lastupdated"].replace("T"," "))
			if current["type"] == "ZLLLightLevel":
				device_specific = "{0};{1}".format(
					current["state"]["lightlevel"],
					current["state"]["lastupdated"].replace("T"," "))
			if current["type"] == "CLIPGenericStatus":
				device_specific = "{0};{1}".format(
					current["state"]["status"],
					current["state"]["lastupdated"].replace("T"," "))

			# device_config = json.dumps(current["config"])

			device_line = "{0};{1}".format(device_data, device_specific)
			results_parsed.append(device_line)
		except Exception as e:
			print "Device with invalid JSON contents found. Error: {0}".format(e)

	return results_parsed


initialize_db()
# Main loop
while True:
	# Retrieve Hue data
	result = retrieve_data("sensors")

	# Parse data
	result_parsed = parse_results(result)
	print(result_parsed)

	# Retrieve and add KNMI data
	knmi = retrieve_knmi_weather_parent()
	if knmi is not False:
		result_parsed = result_parsed + knmi

	# Write to CSV
	if WRITE_FILE:
		write_file(OUT_FILE, result_parsed)

	# Write to DB
	write_db(result_parsed)

	# Finished
	print "Wrote results for {0} devices. Continueing...".format(len(result_parsed))
	
	# Sleep, continue
	time.sleep(INTERVAL)
