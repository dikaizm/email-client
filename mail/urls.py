from django.urls import path

from .views import index

urlpatterns = [
    path('', index.index, name='index'),
    path('login', index.login_view, name='login'),
    path('logout', index.logout_view, name='logout'),
    path('register', index.register, name='register'),

    # API Routes
    path('emails', index.compose_view, name='compose'),
    path('emails/<int:email_id>', index.email, name='email'),
    path('emails/<str:mailbox>', index.mailbox, name='mailbox'),
    
    path('api/security/generate', index.generate_key_view, name='generate_key'),
    path('api/security/keys', index.user_keys_view, name='user_keys'),
    path('api/security/keys/<str:key_id>', index.user_key_item_view, name='user_key_item'),
]