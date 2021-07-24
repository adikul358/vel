from datetime import datetime, timedelta
import csv
from dateutil import tz
from pymongo import MongoClient
client = MongoClient("mongodb://admin:lorem@148.72.212.83:27017/?authSource=admin")
db = client.vel

periods_global = []
slots_global = []
weekdays = ["MON", "TUE", "WED", "THU", "FRI", "SAT", "SUN"]

def next_monday():
    return datetime.now() + timedelta((0 - datetime.now().weekday()) % 7)

def parse_slots(start_raw: list, end_raw: list):
	if len(start_raw) != len(end_raw): 
		raise RuntimeError("Incorrect slots input, starting and ending slots not equal in number")
	
	start_raw = start_raw[1:]
	end_raw = end_raw[1:]
	
	for i in range(len(start_raw)):
		start_time = timedelta(hours=int(start_raw[i][0:2]), minutes=int(start_raw[i][2:4]))
		end_time = timedelta(hours=int(end_raw[i][0:2]), minutes=int(end_raw[i][2:4]))
		slots_global.append((start_time, end_time))


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
		if i[0] == "": 
			s += 1
			continue

		period_curr = {
			'name': i[0].strip(),
			'start': (starting_date + timedelta(days=offset) + slots_global[s][0]).strftime("%Y-%m-%d %H:%M:%S%z"),
			'end': (starting_date + timedelta(days=offset) + slots_global[s][1]).strftime("%Y-%m-%d %H:%M:%S%z"),
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

nm_prompt = next_monday()
starting_date = input(f'Date of Reference Monday ({nm_prompt.strftime("%Y-%m-%d")}): ')
if starting_date == "": 
	starting_date = nm_prompt
elif datetime.strptime(starting_date, "%Y-%m-%d").strftime("%w") != "1":
	raise ValueError("Entered date not a Monday")
else: 
	starting_date = datetime.strptime(starting_date, "%Y-%m-%d")

starting_date = starting_date.replace(tzinfo=tz.tzoffset('IST', 5.5*60*60))

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
	
tt_entry = {
	"starting_date": datetime.strftime(starting_date, "%d %b %Y"),
	"periods_raw": periods_global
}

result = db.tts.insert_one(tt_entry)
print('Created timetable entry for {0} ({1})'.format(starting_date.strftime("%d %b %Y"),result.inserted_id))