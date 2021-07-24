from datetime import datetime, timedelta
from os import system
import csv
import json
import copy
from dateutil import tz
from flask import Flask, request
from flask_cors import CORS, cross_origin

periods_global = []
slots_global = []
starting_date = datetime(2021,7,19)
starting_date = starting_date.replace(tzinfo=tz.tzoffset('IST', 5.5*60*60))
weekdays = ["MON", "TUE", "WED", "THU", "FRI", "SAT", "SUN"]

# Flask API Setup
app = Flask(__name__)
cors = CORS(app)
app.config['CORS_HEADERS'] = 'Content-Type'

# Parse slots array with timings and period numbers.
#
# INPUT: csv data
# OUTPUT: [slots]
def parse_slots(start_raw: list, end_raw: list):
	if len(start_raw) != len(end_raw): 
		raise RuntimeError("Incorrect slots input, starting and ending slots not equal in number")
	
	start_raw = start_raw[1:]
	end_raw = end_raw[1:]
	
	for i in range(len(start_raw)):
		start_time = timedelta(hours=int(start_raw[i][0:2]), minutes=int(start_raw[i][2:4]))
		end_time = timedelta(hours=int(end_raw[i][0:2]), minutes=int(end_raw[i][2:4]))
		slots_global.append((start_time, end_time))


# Parse all periods with all special symbols (@, !) and assign properties (slots, section, universal).
#
# INPUT: csv data
# OuTPUT: [periods]
def parse_periods(periods_raw: list):
	day = periods_raw[0]
	periods_raw = periods_raw[1:]
	periods = []

	for slot in periods_raw:
		slot = slot.strip()
		for i in slot.split("\n\n"): periods.append(i.strip())

	s = 0
	offset = weekdays.index(day)
	for i in periods:
		i = i.split("\n")
		if i[0] == "": continue

		period_curr = {
			'name': i[0].strip(),
			'start': starting_date + timedelta(days=offset) + slots_global[s][0],
			'end': starting_date + timedelta(days=offset) + slots_global[s][1],
			'desc': "\n".join(i[1:]).strip(),
			'assign': "subject"
		}

		if period_curr['name'][0] == '@':
			period_curr['assign'] = 'all'
			period_curr['name'] = period_curr['name'][1:]

		if period_curr['desc'] != "" and period_curr['desc'][0] == '!':
			x = period_curr['desc'].split("!")
			period_curr['desc'] = {}
			for i in x[1:]: 
				a = i.split("\n")
				period_curr['desc'][a[0]] = a[1]

		periods_global.append(period_curr)
		s += 1
		s = s % len(slots_global)
	return 0
	

# Generate person-specific periods according to selected class section and subjects.
#
# INPUT: (section, [subjects])
# OUTPUT: [periods]
def generate_periods(section: str, subjects: list):
	return 0


# Generate .ics file from generated periods
#
# INPUT: [periods]
# OUTPUT: <UID>.ics file
def generate_ics(periods_raw: list):
	return 0

@app.route('/api/ics', methods=['POST'])
@cross_origin()
def ics():
	request_data = request.get_json()
	req_section = request_data['section']
	req_subjects = request_data['subjects']
	periods_copy = copy.deepcopy(periods_global)
	data = []

	print(periods_global[0])

	for i in periods_copy:
		if i['assign'] == "all" or i['name'].lower() in req_subjects:
			if type(i['desc']) == type({}):
				if i['desc'][req_section]:
					i['desc'] = i['desc'][req_section]
			data.append(i)

	return {'data': data}, 200

with open('vel_w30.csv') as csv_file:
	csv_reader = csv.reader(csv_file, delimiter=',')
	line_count = 0
	slots_start_row = []
	slots_end_row = []
	for row in csv_reader:
		line_count += 1
		if line_count == 1:
			slots_start_row = row
		elif line_count == 2:
			slots_end_row = row
			parse_slots(slots_start_row, slots_end_row)

		else:
			parse_periods(row)

# subjects = []
# for i in periods_global:
# 	i["start"] = i["start"].strftime("%Y-%m-%d %H:%M:%S%z")
# 	i["end"] = i["end"].strftime("%Y-%m-%d %H:%M:%S%z")
# 	if i['assign'] == "subject": subjects.append(i['name'])

# subjects = sorted(list(set(subjects)))
# with open("vel.html", "w") as f:
# 	for i in subjects: f.writelines("<option value=\"%s\">%s</option>\n" % (i.lower(), i))

# with open("vel.json", "w") as f:
# 	json.dump(periods_global, f)
if __name__ == "__main__":
    app.run(host='0.0.0.0')
