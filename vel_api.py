from datetime import datetime, timedelta
from ics import Calendar, Event
from ics.alarm import DisplayAlarm
from flask import Flask, request, send_from_directory
from pymongo import MongoClient
from uuid import uuid1

client = MongoClient("mongodb://admin:lorem@148.72.212.83:27017/?authSource=admin")
db = client.vel
tts_col = db['tts']
log_col = db['log']


def log_stat(starting_date: str, section: str, subjects: list):
	result = log_col.insert_one({
		"starting_date": starting_date,
		"section": section,
		"subjects": subjects,
	})
	print(f'Logged Entry for {section}. {result.inserted_id}')

	return 1


def generate_periods(starting_date: str, section: str, subjects: list):
	periods_raw = tts_col.find_one({"starting_date": starting_date})['periods_raw']
	periods_out = []
	for i in periods_raw:
		if i['assign'] == "all" or i['name'].lower() in subjects:
			if type(i['desc']) == type({}):
				if i['desc'][section]:
					i['desc'] = i['desc'][section]
			periods_out.append(i)

	return periods_out


def generate_ics(periods_in: list):
	c = Calendar()
	for i in periods_in:
		e = Event()
		e.name = i['name']
		e.begin = i['start']
		e.end = i['end']
		e.description = i['desc']
		e.alarms = [DisplayAlarm(trigger=timedelta(minutes=-5)), DisplayAlarm(trigger=datetime.strptime(i['start'], "%Y-%m-%d %H:%M:%S%z"))]
		c.events.add(e)
	
	ics_filename = f'{uuid1().hex}.ics'
	ics_file = open(f'gen-csv/{ics_filename}', 'w')
	ics_file.writelines(c)

	return ics_filename


# ===============================================================================

# Flask API Setup
app = Flask(__name__)
app.config["CLIENT_CSV"] = "/var/www/vel/gen-csv/"

# API Endpoint: Return available timetables
@app.route('/api/tts', methods=['POST'])
def tts():
	data = []
	cursor = tts_col.find({})
	for doc in cursor:
		data.append(datetime.strptime(doc['starting_date'], "%d %b %Y"))

	data = sorted(data, reverse=True)
	data = [i.strftime("%d %b %Y") for i in data]

	return {'data': data}, 200
if __name__ == "__main__":
    app.run(host='0.0.0.0')

# API Endpoint: Take form data and return ICS file
@app.route('/api/ics', methods=['POST'])
def ics():
	request_data = request.get_json()
	req_date = request_data['date']
	req_section = request_data['section']
	req_subjects = request_data['subjects']

	periods = generate_periods(req_date, req_section, req_subjects)
	ics_file = generate_ics(periods)

	log_result = log_stat(req_date, req_section, req_subjects)

	print(f'Sending file {app.config["CLIENT_CSV"]}{ics_file}')
	return send_from_directory(directory=app.config["CLIENT_CSV"], path=ics_file, as_attachment=True), 200



if __name__ == "__main__":
    app.run(host='0.0.0.0')