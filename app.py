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

    # 取得今天早上8點和晚上10點之前的時間範圍
    now = datetime.datetime.now(TARGET_TIMEZONE)
    start_of_day = now.replace(hour=0, minute=0, second=0, microsecond=0).astimezone(pytz.utc).strftime('%Y-%m-%dT%H:%M:%S.%fZ')
    end_of_day = now.replace(hour=23, minute=59, second=59, microsecond=0).astimezone(pytz.utc).strftime('%Y-%m-%dT%H:%M:%S.%fZ')

    # 取得今天的所有事件
    events_result = calendar_service.events().list(calendarId='primary', timeMin=start_of_day, timeMax=end_of_day, singleEvents=True, orderBy='startTime').execute()
    events = events_result.get('items', [])

    # 計算可安排的時段
    event_list = []
    start_time = start_of_day
    for event in events:
        event_start = event['start'].get('dateTime', event['start'].get('date'))
        event_start = datetime.datetime.fromisoformat(event_start).astimezone(TARGET_TIMEZONE)
        event_end = event['end'].get('dateTime', event['end'].get('date'))
        event_end = datetime.datetime.fromisoformat(event_end).astimezone(TARGET_TIMEZONE)

        if start_time < event_start:
            end_time = event_start
            event_list.append({'start_time': start_time.strftime('%H:%M'), 'end_time': end_time.strftime('%H:%M'), 'title': 'No event scheduled'})
        start_time = event_end

    if start_time < end_of_day:
        end_time = end_of_day
        event_list.append({'start_time': start_time.strftime('%H:%M'), 'end_time': end_time.strftime('%H:%M'), 'title': 'No event scheduled'})

    return jsonify({'events': event_list})

if __name__ == '__main__':
    app.run()
