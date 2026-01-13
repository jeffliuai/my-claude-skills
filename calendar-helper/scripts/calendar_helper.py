#!/usr/bin/env python3
"""
Google Calendar Helper
完整功能的 Calendar 事件管理工具
"""

import os
import sys
import json
import pickle
from datetime import datetime, timedelta
from pathlib import Path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

import pytz
from dateutil import parser as date_parser

# 權限範圍
SCOPES = ['https://www.googleapis.com/auth/calendar']

# 檔案路徑
SCRIPT_DIR = Path(__file__).parent
CREDENTIALS_FILE = SCRIPT_DIR.parent / 'credentials.json'
TOKEN_FILE = SCRIPT_DIR.parent / 'token.pickle'

class CalendarHelper:
    """Google Calendar 助手"""
    
    def __init__(self):
        self.service = None
        self.timezone = 'Asia/Taipei'  # 預設時區
        
    def authenticate(self):
        """OAuth 認證"""
        creds = None
        
        # 檢查是否有已存在的 token
        if TOKEN_FILE.exists():
            with open(TOKEN_FILE, 'rb') as token:
                creds = pickle.load(token)
        
        # 如果沒有有效的憑證，進行認證
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    str(CREDENTIALS_FILE), SCOPES
                )
                creds = flow.run_local_server(port=0)
            
            # 儲存憑證
            with open(TOKEN_FILE, 'wb') as token:
                pickle.dump(creds, token)
        
        self.service = build('calendar', 'v3', credentials=creds)
        return True
    
    def create_event(self, event_data):
        """
        建立 Calendar 事件
        
        event_data 格式：
        {
            'summary': '事件標題',
            'description': '事件描述',
            'location': '地點',
            'start': '2026-01-15T15:00:00',  # 或 datetime 物件
            'end': '2026-01-15T16:00:00',    # 或 datetime 物件
            'attendees': ['email1@example.com', 'email2@example.com'],
            'reminders': [15, 60],  # 提前 15 分鐘和 1 小時提醒
            'recurrence': 'RRULE:FREQ=WEEKLY;BYDAY=MO'  # 重複規則（選用）
        }
        """
        try:
            # 處理時間
            start_time = self._parse_datetime(event_data.get('start'))
            end_time = self._parse_datetime(event_data.get('end'))
            
            # 如果沒有結束時間，預設 1 小時
            if not end_time:
                end_time = start_time + timedelta(hours=1)
            
            # 建立事件物件
            event = {
                'summary': event_data.get('summary', '無標題事件'),
                'location': event_data.get('location', ''),
                'description': event_data.get('description', ''),
                'start': {
                    'dateTime': start_time.isoformat(),
                    'timeZone': self.timezone,
                },
                'end': {
                    'dateTime': end_time.isoformat(),
                    'timeZone': self.timezone,
                },
            }
            
            # 加入參加者
            if event_data.get('attendees'):
                event['attendees'] = [
                    {'email': email} for email in event_data['attendees']
                ]
            
            # 加入提醒
            if event_data.get('reminders'):
                event['reminders'] = {
                    'useDefault': False,
                    'overrides': [
                        {'method': 'popup', 'minutes': minutes}
                        for minutes in event_data['reminders']
                    ],
                }
            
            # 加入重複規則
            if event_data.get('recurrence'):
                event['recurrence'] = [event_data['recurrence']]
            
            # 建立事件
            created_event = self.service.events().insert(
                calendarId='primary',
                body=event,
                sendUpdates='all' if event_data.get('attendees') else 'none'
            ).execute()
            
            return {
                'success': True,
                'event_id': created_event['id'],
                'html_link': created_event.get('htmlLink'),
                'summary': created_event['summary'],
                'start': created_event['start'].get('dateTime'),
            }
            
        except HttpError as error:
            return {
                'success': False,
                'error': str(error)
            }
    
    def _parse_datetime(self, dt_input):
        """解析時間輸入"""
        if isinstance(dt_input, datetime):
            return dt_input
        
        if isinstance(dt_input, str):
            # 嘗試解析 ISO 格式
            try:
                dt = date_parser.parse(dt_input)
                # 如果沒有時區，加上預設時區
                if dt.tzinfo is None:
                    tz = pytz.timezone(self.timezone)
                    dt = tz.localize(dt)
                return dt
            except:
                pass
        
        # 預設為現在
        tz = pytz.timezone(self.timezone)
        return datetime.now(tz)
    
    def parse_natural_language(self, text):
        """
        智能解析自然語言
        
        範例：
        - "明天下午 3 點和 John 開會"
        - "下週三 10:00-11:00 討論 Q1 計畫"
        """
        # 這裡簡化實作，實際可以用更複雜的 NLP
        event_data = {
            'summary': text,
            'start': None,
            'end': None,
            'attendees': [],
        }
        
        # 提取時間（簡化版）
        now = datetime.now(pytz.timezone(self.timezone))
        
        # 簡單的關鍵字匹配
        if '明天' in text:
            event_data['start'] = now + timedelta(days=1)
        elif '下週' in text:
            event_data['start'] = now + timedelta(weeks=1)
        elif '今天' in text:
            event_data['start'] = now
        else:
            event_data['start'] = now
        
        # 提取標題（移除時間相關字詞）
        summary = text
        for keyword in ['明天', '下週', '今天', '和', '開會', '討論']:
            summary = summary.replace(keyword, '')
        event_data['summary'] = summary.strip()
        
        return event_data

def main():
    """主函數"""
    if len(sys.argv) < 2:
        print(json.dumps({
            'error': '請提供操作類型：create, parse'
        }))
        sys.exit(1)
    
    operation = sys.argv[1]
    
    # 初始化
    helper = CalendarHelper()
    
    # 認證
    if not helper.authenticate():
        print(json.dumps({
            'error': '認證失敗'
        }))
        sys.exit(1)
    
    if operation == 'create':
        # 從 stdin 讀取 JSON 資料
        event_data = json.loads(sys.stdin.read())
        result = helper.create_event(event_data)
        print(json.dumps(result, ensure_ascii=False))
    
    elif operation == 'parse':
        # 解析自然語言
        text = sys.argv[2] if len(sys.argv) > 2 else sys.stdin.read()
        event_data = helper.parse_natural_language(text)
        print(json.dumps(event_data, ensure_ascii=False, default=str))
    
    else:
        print(json.dumps({
            'error': f'未知操作：{operation}'
        }))
        sys.exit(1)

if __name__ == '__main__':
    main()
