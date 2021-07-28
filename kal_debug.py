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

creds = client.GoogleCredentials.from_json(json_token)
http = creds.authorize(httplib2.Http())
try: 
    service = build('calendar', 'v3', credentials=creds)
except client.AccessTokenCredentialsError:
    print("Access token expired")
    creds.refresh(http)
    if creds.to_json() != print("Access token refreshed")
    user_col.update_one(
        {'email': 'kalyaani.manoj@gmail.com'},
        {'$set': {'json_token': creds.to_json()}}
    )
    print("Credentials updated in database")
    service = build('calendar', 'v3', credentials=creds)

page_token = None
vel_calendar_id = ""
while True:
  calendar_list = service.calendarList().list(pageToken=page_token).execute()
  for calendar_list_entry in calendar_list['items']:
    calendar_summary = calendar_list_entry['summary']
    # print(calendar_summary)
    if calendar_summary == "VEL":
      vel_calendar_id = calendar_list_entry['id']
      print(f'vel_calendar_id: {vel_calendar_id}')
      break
  page_token = calendar_list.get('nextPageToken')
  if not page_token: break

if not vel_calendar_id: raise RuntimeError("VEL calendar not present")

page_token = None
while True:
  events = service.events().list(calendarId=vel_calendar_id, pageToken=page_token).execute()
  for event in events['items']:
    print(event['summary'])
  page_token = events.get('nextPageToken')
  if not page_token:
    break
