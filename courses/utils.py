import firebase_admin
from firebase_admin import credentials, messaging
import os
from django.conf import settings

def send_push_notification(fcm_token, title, body, lesson_id, data=None):
    """
    Sends a push notification to a specific device via FCM token.
    lesson_id is REQUIRED now to open the correct video on click.
    """
    # --- INTERNAL INITIALIZATION ---
    try:
        firebase_admin.get_app()
    except ValueError:
        path_to_json = os.path.join(settings.BASE_DIR, 'firebase-credentials.json')
        if os.path.exists(path_to_json):
            cred = credentials.Certificate(path_to_json)
            firebase_admin.initialize_app(cred)
        else:
            print(f"❌ ERROR: {path_to_json} file missing!")
            return False

    try:
        # Data payload preparation
        payload_data = data or {}
        payload_data.update({
            "title": str(title),
            "body": str(body),
            "click_action": "FLUTTER_NOTIFICATION_CLICK",
            # ✅ LESSON_ID: Isse Flutter ko pata chalega kaunsa video kholna hai
            "lesson_id": str(lesson_id), 
        })

        message = messaging.Message(
            notification=messaging.Notification(
                title=str(title),
                body=str(body),
            ),
            data=payload_data,
            token=fcm_token,
            android=messaging.AndroidConfig(
                priority='high',
                notification=messaging.AndroidNotification(
                    channel_id='high_importance_channel',
                    click_action='FLUTTER_NOTIFICATION_CLICK',
                    default_sound=True,
                ),
            ),
        )

        response = messaging.send(message)
        print(f'✅ Firebase Response: {response}')
        return True

    except Exception as e:
        print(f'❌ Firebase Sending Error: {e}')
        return False