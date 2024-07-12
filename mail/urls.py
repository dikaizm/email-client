from django.urls import path

from .views import index
from .views import auth_google

urlpatterns = [
    path('', index.index, name='index'),
    path('login', index.login_view, name='login'),
    path('login/oauth/callback', auth_google.GoogleLoginApi.as_view(), name='google-login-callback'),
    path('login/oauth/redirect', auth_google.GoogleLoginRedirectApi.as_view(), name='google-login-redirect'),
    
    path('api/auth/email-validation', index.email_validation_api, name='email_validation'),
    
    path('logout', index.logout_view, name='logout'),
    # path('register', index.register_view, name='register'),

    # View Routes
    path('compose', index.compose_view, name='compose'),
    path('inbox', index.inbox_view, name='inbox'),
    path('sent', index.sent_view, name='sent'),
    path('security', index.security_view, name='security'),
    
    # API Routes
    path('api/email/refresh/<str:label>', index.refresh_emails_api, name='refresh_emails'),
    path('api/email/find-pubkey/<str:email>', index.find_recipient_pubkey_api, name='find_recipient_pubkey'),
    path('api/email/send', index.compose2_api, name='send_email'),
    path('api/email/inbox', index.inbox_api, name='inbox_api'),
    path('api/email/sent', index.sent_api, name='sent_api'),
    
    path('api/email/<int:email_id>', index.email_detail_api, name='email'),
    path('api/email/decrypt/<int:email_id>', index.decrypt_email_api, name='decrypt_message'),
    
    path('emails/<str:mailbox>', index.mailbox, name='mailbox'),
    
    # PGP Keys
    path('api/security/generate', index.generate_key_view, name='generate_key'),
    path('api/security/keys', index.user_keys_view, name='user_keys'),
    path('api/security/keys/<str:key_id>', index.user_key_item_view, name='user_key_item'),
    path('api/security/received-keys', index.received_keys_view, name='received_keys'),
    path('api/security/received-keys/<str:key_id>', index.received_key_item_view, name='received_key_item'),
    path('api/security/request-key', index.request_key_view, name='request_key'),
]