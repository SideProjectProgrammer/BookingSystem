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
creds_filename = 'credentials.json'

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
    events_result = calendar_service.events().list(calendarId='primary', timeMin=start_of_day.isoformat(), timeMax=end_of_day.isoformat(), singleEvents=True, orderBy='startTime').execute()
    events = events_result.get('items', [])

    if not events:
        print('No upcoming events found.')
        return jsonify({'events': []})

    # 計算空閒時間
    busy_times = []
    for event in events:
        start = event['start'].get('dateTime', event['start'].get('date'))
        end = event['end'].get('dateTime', event['end'].get('date'))
        busy_times.append((datetime.datetime.fromisoformat(start).astimezone(TARGET_TIMEZONE), datetime.datetime.fromisoformat(end).astimezone(TARGET_TIMEZONE)))

    # 排序busy_times以方便計算空閒時間
    busy_times.sort()

    # 計算空閒時間
    free_times = []
    if busy_times[0][0] > start_of_day:
        free_times.append((start_of_day, busy_times[0][0]))
    for i in range(len(busy_times) - 1):
        if busy_times[i][1] < busy_times[i + 1][0]:
            free_times.append((busy_times[i][1], busy_times[i + 1][0]))
    if busy_times[-1][1] < end_of_day:
        free_times.append((busy_times[-1][1], end_of_day))

    # 回傳空閒時間
    free_time_list = []
    for free_time in free_times:
        free_time_str = '{} - {}'.format(free_time[0].strftime('%H:%M'), free_time[1].strftime('%H:%M'))
        free_time_list.append(free_time_str)

    return jsonify({'free_time': free_time_list})

if __name__ == '__main__':
    app.run()
