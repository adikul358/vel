from pymongo import MongoClient
import httplib2
from oauth2client import client
from googleapiclient.discovery import build
import os
from dotenv import load_dotenv
load_dotenv()

db = MongoClient(f'mongodb://admin:{os.getenv("MONGO_PASSWORD")}@localhost:27017/?authSource=admin').vel
tts_col = db['tts']
log_col = db['log']
users_col = db['users']

user_data = users_col.find_one({'email': 'kalyaani.manoj@gmail.com'})

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
    print(calendar_summary)
    if calendar_summary == "VEL":
      vel_calender_id = calendar_list_entry['id']
      print(f'vel_calender_id: {vel_calender_id}')
      break
  page_token = calendar_list.get('nextPageToken')
  if not page_token: break

page_token = None
while True:
  events = service.events().list(calendarId=vel_calender_id, pageToken=page_token).execute()
  for event in events['items']:
    print(event['summary'])
  page_token = events.get('nextPageToken')
  if not page_token:
    break