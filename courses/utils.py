import firebase_admin
from firebase_admin import credentials, messaging
import os
from django.conf import settings

def send_push_notification(fcm_token, title, body, lesson_id, data=None):
    # --- JWT FIX: FORCE RE-INITIALIZATION ---
    try:
        # Pehle se maujood app ko nikalne ki koshish karein
        app = firebase_admin.get_app()
        firebase_admin.delete_app(app)
    except ValueError:
        pass # App nahi thi, koi baat nahi

    path_to_json = os.path.join(settings.BASE_DIR, 'firebase-credentials.json')
    
    if not os.path.exists(path_to_json):
        print(f"❌ ERROR: {path_to_json} missing!")
        return False

    try:
        cred = credentials.Certificate(path_to_json)
        firebase_admin.initialize_app(cred)
        
        payload_data = data or {}
        payload_data.update({
            "title": str(title),
            "body": str(body),
            "click_action": "FLUTTER_NOTIFICATION_CLICK",
            "lesson_id": str(lesson_id), 
        })

        message = messaging.Message(
            notification=messaging.Notification(title=str(title), body=str(body)),
            data=payload_data,
            token=str(fcm_token),
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
        print(f'✅ Firebase Success: {response}')
        return True

    except Exception as e:
        print(f'❌ Firebase Sending Error: {e}')
        return False