from datetime import datetime, timedelta
from flask.wrappers import Response
from ics import Calendar, Event
from ics.alarm import DisplayAlarm
from flask import Flask, request, send_from_directory
from pymongo import MongoClient
import httplib2
from oauth2client import client
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from uuid import uuid1
import json
import os
from dotenv import load_dotenv
load_dotenv()

SCOPES = ['https://www.googleapis.com/auth/calendar.readonly']

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


def feed_events(creds):
	service = build('calendar', 'v3', credentials=creds)

	now = datetime.utcnow().isoformat() + 'Z'
	events_result = service.events().list(calendarId='primary', timeMin=now,
																			maxResults=10, singleEvents=True,
																			orderBy='startTime').execute()
	events = events_result.get('items', [])

	events_out = []
	if not events:
			return 'No upcoming events found.'
	for event in events:
			start = event['start'].get('dateTime', event['start'].get('date'))
			events_out.append((start, event['summary']))

	return events_out


def add_user(json_token: dict, email: str, user_section: str, user_subjects: list):
	result = users_col.insert_one({
		"json_token": json_token,
		"email": email,
		"section": user_section,
		"subjects": user_subjects
	})
	print(f'Added user {email}')

	return 1


def check_user(email: str):
	result = users_col.find_one({"email": email,})
	if result: return result

	return False

# ===============================================================================

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
	request_data = request.get_data()
	print("Success, data received")
	print(request_data)

	if not request.headers.get('X-Requested-With'): return Response(status=403)

	CREDENTIALS = client.credentials_from_clientsecrets_and_code(
		os.getenv('CLIENT_SECRET_FILE'),
		['https://www.googleapis.com/auth/calendar.events', 'profile', 'email'],
		request_data
	)

	if not check_user(CREDENTIALS.id_token['email']): 
		add_user(CREDENTIALS.to_json(), CREDENTIALS.id_token['email'], "", [])

	return {"email": CREDENTIALS.id_token['email']}, 200

# API Endpoint: Feed events in to user's Google Calendar
@app.route('/api/integrate', methods=['POST'])
def integrate():
	request_data = request.get_json()
	req_email = request_data['email']
	req_subjects = request_data['subjects']
	req_section = request_data['section']

	result = users_col.update(
		{'email': req_email},
		{'subjects': req_subjects, 'section': req_section}
	)

	cred_json = users_col.find_one({'email': req_email}, {'json_token':1})
	CREDENTIALS = client.Credentials.from_json(cred_json)

	return feed_events(CREDENTIALS)


if __name__ == "__main__":
    app.run(host='0.0.0.0',port=5001)