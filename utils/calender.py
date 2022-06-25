from __future__ import print_function

import datetime
import os.path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# If modifying these scopes, delete the file token.json.
SCOPES = ['https://www.googleapis.com/auth/calendar.events',
          'https://www.googleapis.com/auth/calendar']


def main():
    """Shows basic usage of the Google Calendar API.
    Prints the start and name of the next 10 events on the user's calendar.
    """
    creds = None
    # The file token.json stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'client_secret_757249550479-057dbi6c1544ga1f7ph353omcdt09t8f.apps.googleusercontent.com.json', SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open('token.json', 'w') as token:
            token.write(creds.to_json())

    service = build("calendar", "v3", credentials=creds)
    calendarId = "primary"
    event = {
        "start": {
            "dateTime": "2022-01-01T00:00:00.000+07:00",
        },
        "end": {
            "dateTime": "2022-01-01T00:30:00.000+07:00",
            'timeZone': 'Asia/Ho_Chi_Minh',
        },
        # "attendees": [{"email": "basicallyarois@gmail.com"}],
        "conferenceData": {
            "createRequest": {"requestId": "sample123", "conferenceSolutionKey": {"type": "hangoutsMeet"}}},
        "summary": "Meet Event",
        "description": "Description"
    }
    res = service.events().insert(calendarId=calendarId, sendNotifications=True, body=event,
                                  conferenceDataVersion=1).execute()

    print(res)


if __name__ == '__main__':
    main()