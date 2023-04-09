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
    now = datetime.datetime.utcnow().isoformat() + 'Z'  # 'Z' indicates UTC time

    # 取得前 10 個事件
    events_result = calendar_service.events().list(calendarId='primary', timeMin=now, maxResults=10, singleEvents=True, orderBy='startTime').execute()
    events = events_result.get('items', [])

    if not events:
        print('No upcoming events found.')
        return

    # 回傳預約資訊
    event_list = []
    for event in events:
        start = event['start'].get('dateTime', event['start'].get('date'))
        start_time = datetime.datetime.fromisoformat(start).astimezone(TARGET_TIMEZONE).strftime('%H:%M')
        event_list.append({'title': event['summary'], 'start_time': start_time})

    return jsonify({'events': event_list})

if __name__ == '__main__':
    app.run()
