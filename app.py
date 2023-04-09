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

    # 取得現在時間七天後的時間
    now = datetime.datetime.utcnow()
    end = now + datetime.timedelta(days=7)
    time_min = now.isoformat() + 'Z'
    time_max = end.isoformat() + 'Z'

    # 取得未來七天的事件
    events_result = calendar_service.events().list(calendarId='primary', timeMin=time_min, timeMax=time_max, maxResults=10, singleEvents=True, orderBy='startTime').execute()
    events = events_result.get('items', [])

    if not events:
        print('No upcoming events found.')
        return jsonify({'events': []})

    # 回傳預約資訊
    event_list = []
    for event in events:
        start = event['start'].get('dateTime', event['start'].get('date'))
        start_time = datetime.datetime.fromisoformat(start).astimezone(TARGET_TIMEZONE).strftime('%H:%M')
        event_list.append({'title': event['summary'], 'start_time': start_time})

    return jsonify({'events': event_list})

if __name__ == '__main__':
    app.run()
