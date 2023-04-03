import os
from datetime import datetime, time, timedelta
from google.oauth2.service_account import Credentials
from googleapiclient.errors import HttpError
from googleapiclient.discovery import build
from flask import Flask, jsonify

app = Flask(__name__)

# 從環境變數中讀取 Google 相關變數
SCOPES = ['https://www.googleapis.com/auth/calendar.readonly']
SERVICE_ACCOUNT_EMAIL = os.environ['SERVICE_ACCOUNT_EMAIL']
SERVICE_ACCOUNT_KEY = os.environ['SERVICE_ACCOUNT_KEY'].replace('\\n', '\n')
CALENDAR_ID = os.environ['CALENDAR_ID']
TIMEZONE = os.environ['TIMEZONE']

# 設定 Service Account Credentials
creds = Credentials.from_service_account_info({
    "type": "service_account",
    "project_id": os.environ['PROJECT_ID'],
    "private_key_id": os.environ['PRIVATE_KEY_ID'],
    "private_key": SERVICE_ACCOUNT_KEY,
    "client_email": SERVICE_ACCOUNT_EMAIL,
    "client_id": os.environ['CLIENT_ID'],
    "auth_uri": os.environ['AUTH_URI'],
    "token_uri": os.environ['TOKEN_URI'],
    "auth_provider_x509_cert_url": os.environ['AUTH_PROVIDER_X509_CERT_URL'],
    "client_x509_cert_url": os.environ['CLIENT_X509_CERT_URL']
}, scopes=SCOPES)

# 設定 Calendar API client
calendar_service = build('calendar', 'v3', credentials=creds)


@app.route('/')
def list_todays_events():
    # 設定當天的時間範圍
    today_start = datetime.combine(datetime.today(), time.min).isoformat()
    today_end = datetime.combine(datetime.today(), time.max).isoformat()

    # 使用 Calendar API 取得當天的預約
    try:
        events_result = calendar_service.events().list(calendarId=CALENDAR_ID, timeMin=today_start, timeMax=today_end, singleEvents=True, orderBy='startTime').execute()
        events = events_result.get('items', [])
    except HttpError as error:
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