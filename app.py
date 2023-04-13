import os
import pytz
import datetime
from dateutil import tz
from google.oauth2.service_account import Credentials
from googleapiclient.errors import HttpError
from googleapiclient.discovery import build
from flask import Flask, jsonify
import json

app = Flask(__name__)

# 從環境變數中讀取 Google 相關變數
SCOPES = ['https://www.googleapis.com/auth/calendar']
CALENDAR_ID = os.environ['CALENDAR_ID']
TIMEZONE = os.environ['TIMEZONE']

# 設定 Service Account Credentials
creds = None
creds_filename = 'service_credentials.json'

if os.path.exists(creds_filename):
    with open(creds_filename, 'r') as f:
        creds_info = json.load(f)
        creds = Credentials.from_service_account_info(creds_info, scopes=SCOPES)

if creds is None:
    print('No credentials found. Exiting...')
    exit()

# 設定 Calendar API client
calendar_service = build('calendar', 'v3', credentials=creds)


@app.route('/')
def list_todays_events():
    # 設定目標時區
    TARGET_TIMEZONE = tz.gettz(os.environ['TIMEZONE'])

    # 取得當前時間
    now = datetime.datetime.utcnow()

    # 設定今天早上 8 點的 UTC 時間
    start_of_day = now.replace(hour=8, minute=0, second=0, microsecond=0, tzinfo=pytz.utc)

    # 設定今天晚上 10 點的 UTC 時間
    end_of_day = now.replace(hour=22, minute=0, second=0, microsecond=0, tzinfo=pytz.utc)

    # 取得今天的事件
    events_result = calendar_service.events().list(
        calendarId=CALENDAR_ID,
        timeMin=start_of_day.isoformat(),
        timeMax=(end_of_day + datetime.timedelta(days=7)).isoformat(),
        singleEvents=True,
        orderBy='startTime'
    ).execute()

    events = events_result.get('items', [])
    return jsonify({'events': start_of_day})
    
    if not events:
        # 如果沒有任何事件發生，直接回傳五個預設時間區間
        return jsonify({'free_time': ['08:00 - 09:59', '10:00 - 11:59', '14:00 - 15:59', '16:00 - 17:59', '19:00 - 20:590']})

    # 計算忙碌時間
    busy_times = []
    for event in events:
        start = event['start'].get('dateTime', event['start'].get('date'))
        end = event['end'].get('dateTime', event['end'].get('date'))
        busy_times.append((datetime.datetime.fromisoformat(start).astimezone(TARGET_TIMEZONE), datetime.datetime.fromisoformat(end).astimezone(TARGET_TIMEZONE)))

    free_time_list = [
        {'time_slot': '08:00 - 09:59', 'free': True},
        {'time_slot': '10:00 - 11:59', 'free': True},
        {'time_slot': '14:00 - 15:59', 'free': True},
        {'time_slot': '16:00 - 17:59', 'free': True},
        {'time_slot': '19:00 - 20:59', 'free': True}
    ]

    for event in events:
        start = event['start'].get('dateTime', event['start'].get('date'))
        end = event['end'].get('dateTime', event['end'].get('date'))
        start_time = datetime.datetime.fromisoformat(start).astimezone(TARGET_TIMEZONE).time()
        end_time = datetime.datetime.fromisoformat(end).astimezone(TARGET_TIMEZONE).time()
        for free_time in free_time_list:
            if start_time < datetime.datetime.strptime(free_time['time_slot'].split(' - ')[1], '%H:%M').time() and end_time < datetime.datetime.strptime(free_time['time_slot'].split(' - ')[0], '%H:%M').time():
                free_time['free'] = True
            elif start_time > datetime.datetime.strptime(free_time['time_slot'].split(' - ')[1], '%H:%M').time() and end_time > datetime.datetime.strptime(free_time['time_slot'].split(' - ')[0], '%H:%M').time():
                free_time['free'] = True
            else:
                free_time['free'] = False


    free_time_list = [free_time['time_slot'] for free_time in free_time_list if free_time['free']]

    return jsonify({'free_time': busy_times})

if __name__ == '__main__':
    app.run()
