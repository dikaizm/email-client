from typing import Any, Dict

import google_auth_oauthlib.flow
import jwt
import requests
from attrs import define
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured, ValidationError
from django.urls import reverse_lazy
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request

from mail.models import User, UserOAuthToken

@define
class GoogleSdkLoginCredentials:
    client_id: str
    client_secret: str
    project_id: str


@define
class GoogleAccessTokens:
    id_token: str
    access_token: str
    payload_token: Dict[str, Any]

    def decode_id_token(self) -> Dict[str, Any]:
        id_token = self.id_token
        decoded_token = jwt.decode(jwt=id_token, options={"verify_signature": False})
        return decoded_token


class GoogleSdkLoginFlowService:
    API_URI = reverse_lazy("google-login-callback")

    # Two options are available: 'web', 'installed'
    GOOGLE_CLIENT_TYPE = "web"

    GOOGLE_AUTH_URL = "https://accounts.google.com/o/oauth2/auth"
    GOOGLE_ACCESS_TOKEN_OBTAIN_URL = "https://oauth2.googleapis.com/token"
    GOOGLE_USER_INFO_URL = "https://www.googleapis.com/oauth2/v3/userinfo"

    # Add auth_provider_x509_cert_url if you want verification on JWTS such as ID tokens
    GOOGLE_AUTH_PROVIDER_CERT_URL = ""

    SCOPES = [
        "https://www.googleapis.com/auth/userinfo.email",
        "https://www.googleapis.com/auth/userinfo.profile",
        "openid",
        "https://mail.google.com/"
    ]

    def __init__(self):
        self._credentials = google_sdk_login_get_credentials()

    def _get_redirect_uri(self):
        domain = settings.BASE_BACKEND_URL
        api_uri = self.API_URI
        redirect_uri = f"{domain}{api_uri}"
        return redirect_uri

    def _generate_client_config(self):
        # This follows the structure of the official "client_secret.json" file
        client_config = {
            self.GOOGLE_CLIENT_TYPE: {
                "client_id": self._credentials.client_id,
                "project_id": self._credentials.project_id,
                "auth_uri": self.GOOGLE_AUTH_URL,
                "token_uri": self.GOOGLE_ACCESS_TOKEN_OBTAIN_URL,
                "auth_provider_x509_cert_url": self.GOOGLE_AUTH_PROVIDER_CERT_URL,
                "client_secret": self._credentials.client_secret,
                "redirect_uris": [self._get_redirect_uri()],
                "javascript_origins": [settings.BASE_FRONTEND_URL],
            }
        }
        return client_config

    def get_authorization_url(self):
        redirect_uri = self._get_redirect_uri()
        client_config = self._generate_client_config()

        # Reference: https://developers.google.com/identity/protocols/oauth2/web-server#creatingclient
        google_oauth_flow = google_auth_oauthlib.flow.Flow.from_client_config(
            client_config=client_config, scopes=self.SCOPES
        )
        google_oauth_flow.redirect_uri = redirect_uri

        authorization_url, state = google_oauth_flow.authorization_url(
            access_type="offline",
            include_granted_scopes="true",
            prompt="select_account",
        )
        return authorization_url, state

    def get_tokens(self, *, code: str, state: str) -> GoogleAccessTokens:
        redirect_uri = self._get_redirect_uri()
        client_config = self._generate_client_config()

        flow = google_auth_oauthlib.flow.Flow.from_client_config(
            client_config=client_config, scopes=self.SCOPES, state=state
        )
        flow.redirect_uri = redirect_uri
        access_credentials_payload = flow.fetch_token(code=code)

        if not access_credentials_payload:
            raise ValidationError("Failed to obtain access credentials from Google")

        google_tokens = GoogleAccessTokens(
            id_token=access_credentials_payload["id_token"],
            access_token=access_credentials_payload["access_token"],
            payload_token=access_credentials_payload,
        )

        return google_tokens

    def get_user_info(self, *, google_tokens: GoogleAccessTokens) -> Dict[str, Any]:
        access_token = google_tokens.access_token
        # Reference: https://developers.google.com/identity/protocols/oauth2/web-server#callinganapi
        response = requests.get(self.GOOGLE_USER_INFO_URL, params={"access_token": access_token})

        if not response.ok:
            raise ValidationError("Failed to obtain user info from Google.")

        return response.json()


def google_sdk_login_get_credentials() -> GoogleSdkLoginCredentials:
    client_id = settings.GOOGLE_OAUTH2_CLIENT_ID
    client_secret = settings.GOOGLE_OAUTH2_CLIENT_SECRET
    project_id = settings.GOOGLE_OAUTH2_PROJECT_ID

    if not client_id:
        raise ImproperlyConfigured("GOOGLE_OAUTH2_CLIENT_ID missing in env.")

    if not client_secret:
        raise ImproperlyConfigured("GOOGLE_OAUTH2_CLIENT_SECRET missing in env.")

    if not project_id:
        raise ImproperlyConfigured("GOOGLE_OAUTH2_PROJECT_ID missing in env.")

    credentials = GoogleSdkLoginCredentials(client_id=client_id, client_secret=client_secret, project_id=project_id)

    return credentials


def oauth_get_credentials(user: User):
    try:        
        # Find oauth cred by user
        oauth_token = UserOAuthToken.get_token(user).serialize()
        api_creds = google_sdk_login_get_credentials()
        
        oauth_token['client_id'] = api_creds.client_id
        oauth_token['client_secret'] = api_creds.client_secret
        oauth_token['project_id'] = api_creds.project_id
        
        creds = Credentials.from_authorized_user_info(oauth_token)
    except UserOAuthToken.DoesNotExist:
        raise ValidationError("User has no oauth token.")
    
    # print(creds.to_json())
    
    if creds and creds.valid:
        pass
    
    elif creds and creds.expired and creds.refresh_token:
        creds.refresh(Request())
        # Save the new token
        UserOAuthToken.update_token(user, creds)
        
    return creds