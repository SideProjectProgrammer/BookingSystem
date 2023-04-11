import os
import sys
import pytz
from dateutil import tz
from datetime import datetime, time, timedelta
from google.oauth2.service_account import Credentials
from googleapiclient.errors import HttpError
from googleapiclient.discovery import build
from flask import Flask, jsonify

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
    now = datetime.now(tz=pytz.utc).astimezone(TARGET_TIMEZONE)

    # 取得當天起始時間和結束時間
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0).astimezone(pytz.utc).strftime('%Y-%m-%dT%H:%M:%S.%fZ')
    today_end = now.replace(hour=23, minute=59, second=59, microsecond=0).astimezone(pytz.utc).strftime('%Y-%m-%dT%H:%M:%S.%fZ')

    # 使用 Calendar API 取得當天的預約
    try:
        events_result = calendar_service.events().list(calendarId=CALENDAR_ID, timeMin=today_start, timeMax=today_end, singleEvents=True, orderBy='startTime').execute()
        events = events_result.get('items', [])
    except HttpError as error:
        print('Google Calendar API error:', error)
        print(error.content)
        return jsonify({'error': 'Google Calendar API error: %s' % error}), 500

    # 回傳預約資訊
    event_list = []
    for event in events:
        start = event['start'].get('dateTime', event['start'].get('date'))
        start_time = datetime.fromisoformat(start).strftime('%H:%M')
        event_list.append({'title': event['summary'], 'start_time': start_time})

    return jsonify({'events': event_list})

if __name__ == '__main__':
    app.run()
