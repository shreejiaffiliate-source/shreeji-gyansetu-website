from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from django.contrib import messages

class MySocialAccountAdapter(DefaultSocialAccountAdapter):
    def authentication_error(self, request, provider_id, error=None, exception=None, extra_context=None):
        print(f"DEBUG LOGIN ERROR: {error}, {exception}, {extra_context}")