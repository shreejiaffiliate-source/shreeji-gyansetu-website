import firebase_admin
from firebase_admin import credentials, messaging
import os
from django.conf import settings

# Initialize Firebase only once
path_to_json = os.path.join(settings.BASE_DIR, 'firebase-credentials.json')
cred = credentials.Certificate(path_to_json)
firebase_admin.initialize_app(cred)

def send_push_notification(fcm_token, title, body, data=None):
    """
    Sends a push notification to a specific device via FCM token.
    """
    try:
        message = messaging.Message(
            notification=messaging.Notification(
                title=title,
                body=body,
            ),
            data=data or {}, # Optional: Pass lesson_id or course_slug here
            token=fcm_token,
        )
        response = messaging.send(message)
        print('Successfully sent message:', response)
        return True
    except Exception as e:
        print('Error sending Firebase message:', e)
        return False