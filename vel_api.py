from datetime import datetime, timedelta
from flask.wrappers import Response
from ics import Calendar, Event
from ics.alarm import DisplayAlarm
from flask import Flask, request, send_from_directory
from pymongo import MongoClient
import httplib2
from oauth2client import client
from googleapiclient.discovery import build
from uuid import uuid1
import json
import os
from dotenv import load_dotenv
load_dotenv()

SCOPES = ['https://www.googleapis.com/auth/calendar', 'profile', 'email']

db = MongoClient(f'mongodb://admin:{os.getenv("MONGO_PASSWORD")}@localhost:27017/?authSource=admin').vel
tts_col = db['tts']
log_col = db['log']
users_col = db['users']


def log_stat(starting_date: str, section: str, subjects: list, ics: str):
	result = log_col.insert_one({
		"starting_date": starting_date,
		"section": section,
		"subjects": subjects,
		"ics": ics
	})
	print(f'Logged Entry for {section}. {result.inserted_id}')

	return 1


def generate_periods(starting_date: str, section: str, subjects: list):
	periods_raw = tts_col.find_one({"starting_date": starting_date})['periods_raw']
	periods_out = []
	for i in periods_raw:
		if i['assign'] == "all" or i['name'].lower() in subjects:
			if type(i['desc']) == type({}):
				if section in i['desc'].keys():
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

	if not os.path.exists(os.getenv("CLIENT_ICS")): os.mkdir(os.getenv("CLIENT_ICS"))
	ics_file = open(f'{os.getenv("CLIENT_ICS")}{ics_filename}', 'w')
	ics_file.writelines(c)

	return ics_filename


def feed_events(user_data: dict, starting_date: str):
	json_token = user_data['json_token']
	email = user_data['email']
	section = user_data['section']
	subjects = user_data['subjects']

	creds = client.AccessTokenCredentials.from_json(json_token)
	http = creds.authorize(httplib2.Http())
	service = build('calendar', 'v3', http=http)

	page_token = None
	vel_calender_id = ""
	while True:
		calendar_list = service.calendarList().list(pageToken=page_token).execute()
		for calendar_list_entry in calendar_list['items']:
			calendar_summary = calendar_list_entry['summary']
			if calendar_summary == "VEL":
				vel_calender_id = calendar_list_entry['id']
				break
		page_token = calendar_list.get('nextPageToken')
		if not page_token: break
	if vel_calender_id == "":
		calendar = {'summary': 'VEL'}
		created_calendar = service.calendars().insert(body=calendar).execute()
		vel_calender_id = created_calendar['id']
		created_calendar['defaultReminders'] = [
			{'method': 'popup', 'minutes': 5},
			{'method': 'popup', 'minutes': 0},
		]
		created_calendar['foregroundColor'] = '#ffffff'
		created_calendar['backgroundColor'] = '#111827'
		updated_calendar_list_entry = service.calendarList().update(calendarId=vel_calender_id, colorRgbFormat=True, body=created_calendar).execute()

		result = users_col.update_one(
			{'email': email},
			{'$set': {
				'calenderId': vel_calender_id
			}}
		)
	
	user_periods = generate_periods(starting_date, section, subjects)
	added_events = []

	for i in user_periods:
		event = {
			'summary': i['name'],
			'description': i['desc'],
			'start': {
				'dateTime': datetime.strptime(i['start'], "%Y-%m-%d %H:%M:%S%z").strftime("%Y-%m-%dT%H:%M:%S%z")
			},
			'end': {
				'dateTime': datetime.strptime(i['start'], "%Y-%m-%d %H:%M:%S%z").strftime("%Y-%m-%dT%H:%M:%S%z")
			},
			'reminders': {
				'useDefault': True,
			},
		}
		event = service.events().insert(calendarId=vel_calender_id, body=event).execute()
		added_events.append(event)

	return { "calenderId": vel_calender_id, "added_events": added_events}


def add_user(json_token: dict, email: str, user_section: str, user_subjects: list):
	result = users_col.find_one({"email": email})
	if result:
		del_result = users_col.delete_one({'email': email})
	result = users_col.insert_one({
		"json_token": json_token,
		"email": email,
		"section": user_section,
		"subjects": user_subjects
	})
	print(f'Added user {email}')

	return 1






# Flask API Setup
app = Flask(__name__)

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

# API Endpoint: Take form data and return ICS file
@app.route('/api/ics', methods=['POST'])
def ics():
	request_data = request.get_json()
	req_date = request_data['date']
	req_section = request_data['section']
	req_subjects = request_data['subjects']

	periods = generate_periods(req_date, req_section, req_subjects)
	ics_file = generate_ics(periods)

	# log_result = log_stat(req_date, req_section, req_subjects, ics_file)

	print(f'Sending file {os.getenv("CLIENT_ICS")}{ics_file}')
	return send_from_directory(directory=os.getenv("CLIENT_ICS"), path=ics_file, as_attachment=True), 200

# API Endpoint: Process Google Sign in
@app.route('/api/signin', methods=['POST'])
def signin():
	auth_code = request.get_data()

	if not request.headers.get('X-Requested-With'): return Response(status=403)
	CREDENTIALS = client.credentials_from_clientsecrets_and_code(os.getenv('CLIENT_SECRET_FILE'), SCOPES, auth_code)

	add_user(CREDENTIALS.to_json(), CREDENTIALS.id_token['email'], "", [])

	return {"email": CREDENTIALS.id_token['email']}, 200

# API Endpoint: Feed events in to user's Google Calendar
@app.route('/api/integrate', methods=['POST'])
def integrate():
	request_data = request.get_json()
	req_email = request_data['email']
	req_subjects = request_data['subjects']
	req_section = request_data['section']
	req_date = request_data['date']

	result = users_col.update_one(
		{'email': req_email},
		{'$set': {
			'subjects': req_subjects, 
			'section': req_section
		}}
	)

	user_data = users_col.find_one({'email': req_email})
	return Response(json.dumps(feed_events(user_data, req_date)))


if __name__ == "__main__":
    app.run(host='0.0.0.0',port=5001)