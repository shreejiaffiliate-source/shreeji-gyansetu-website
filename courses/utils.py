import firebase_admin
from firebase_admin import credentials, messaging
import os
from django.conf import settings

def send_push_notification(fcm_token, title, body, lesson_id, data=None):
    # --- JWT FIX: FORCE RE-INITIALIZATION ---
    try:
        app = firebase_admin.get_app()
        firebase_admin.delete_app(app)
    except ValueError:
        pass 

    path_to_json = os.path.join(settings.BASE_DIR, 'firebase-credentials.json')
    
    if not os.path.exists(path_to_json):
        print(f"❌ ERROR: {path_to_json} missing!")
        return False

    try:
        cred = credentials.Certificate(path_to_json)
        firebase_admin.initialize_app(cred)
        
        payload_data = data or {}
        # Ensure lesson_id is always there
        payload_data.update({
            "title": str(title),
            "body": str(body),
            "click_action": "FLUTTER_NOTIFICATION_CLICK",
            "lesson_id": str(lesson_id), 
        })

        # ✅ Loop through data to ensure all values are STRINGS (FCM requirement)
        final_data = {k: str(v) for k, v in payload_data.items()}

        message = messaging.Message(
            notification=messaging.Notification(title=str(title), body=str(body)),
            data=final_data, # Use the cleaned string data
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