from datetime import datetime
from django.contrib.auth.models import AbstractUser
from django.utils import timezone
from django.db import models
import pytz


class User(AbstractUser):
    def __str__(self):
        return f'{self.username}'
    
    def get_user_by_email(email):
        try:
            return User.objects.get(email=email)
        except User.DoesNotExist:
            return None
        
    def create_user(email, password, first_name=None, last_name=None, **extra_fields):
        user = User.objects.create_user(email, email, password, first_name=first_name, last_name=last_name, **extra_fields)
        user.save()
        return user
    
    def activate_user(self):
        self.is_active = True
        self.save()
        return self


class UserConfig(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='config')
    incoming_server = models.CharField(max_length=255)
    incoming_port = models.IntegerField()
    incoming_security = models.CharField(max_length=255)
    outgoing_server = models.CharField(max_length=255)
    outgoing_port = models.IntegerField()
    outgoing_security = models.CharField(max_length=255)
    created = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'mail_user_configs'
        indexes = [
            models.Index(fields=['user']),
        ]
        
    def serialize(self):
        return {
            'incoming_server': self.incoming_server,
            'incoming_port': self.incoming_port,
            'incoming_security': self.incoming_security,
            'outgoing_server': self.outgoing_server,
            'outgoing_port': self.outgoing_port,
            'outgoing_security': self.outgoing_security,
            'created': self.created.strftime('%b %d %Y, %I:%M %p')
        }


class UserOAuthToken(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='oauth_token')
    id_token = models.TextField()
    access_token = models.TextField()
    refresh_token = models.TextField()
    expires_in = models.IntegerField()
    expires_at = models.DateTimeField()
    token_type = models.CharField(max_length=255)
    created = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'mail_user_oauth_tokens'
        indexes = [
            models.Index(fields=['user']),
        ]
        
    def serialize(self):
        return {
            'id_token': self.id_token,
            'access_token': self.access_token,
            'refresh_token': self.refresh_token,
            'expires_in': self.expires_in,
            'expires_at': self.expires_at.strftime('%b %d %Y, %I:%M %p'),
            'token_type': self.token_type,
            'created': self.created.strftime('%b %d %Y, %I:%M %p')
        }
        
    def create_token(user, token):
        expires_at = datetime.fromtimestamp(token["expires_at"])
        
        token = UserOAuthToken.objects.create(
            user=user,
            id_token=token["id_token"],
            access_token=token["access_token"],
            refresh_token=token["refresh_token"],
            expires_in=token["expires_in"],
            token_type=token["token_type"],
            expires_at=expires_at
        )
        return token


class Email(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='emails')
    sender = models.ForeignKey(User, on_delete=models.PROTECT, related_name='emails_sent')
    recipients = models.ManyToManyField(User, related_name='emails_received')
    subject = models.CharField(max_length=255)
    body = models.TextField(blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    read = models.BooleanField(default=False)
    archived = models.BooleanField(default=False)
    encrypted = models.BooleanField(default=False)
    signed = models.BooleanField(default=False)

    def serialize(self):
        tz = pytz.timezone('Asia/Bangkok')
        timestamp_date = self.timestamp.astimezone(tz)
        
        return {
            'id': self.id,
            'sender': self.sender.email,
            'recipients': [user.email for user in self.recipients.all()],
            'subject': self.subject,
            'body': self.body,
            'timestamp': timestamp_date.strftime('%b %d %Y, %I:%M %p'),
            'read': self.read,
            'archived': self.archived,
            'encrypted': self.encrypted,
            'signed': self.signed,
        }


class EmailHMAC(models.Model):
    email = models.OneToOneField(Email, on_delete=models.CASCADE, related_name='hmac')
    hmac = models.TextField(db_index=True)
    secret_key = models.CharField(max_length=255, db_index=True)
    created = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'mail_email_hmacs'

    def serialize(self):
        return {
            'email': self.email.id,
            'hmac': self.hmac,
            'secret_key': self.secret_key,
            'created': self.created.strftime('%b %d %Y, %I:%M %p')
        }


class PGPKey(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='pgp_keys')
    # key_id = models.CharField(max_length=255, db_index=True, unique=True, null=True, blank=True)
    key_id = models.CharField(max_length=255, db_index=True, unique=True)
    private_key = models.TextField()
    public_key = models.TextField()
    key_size = models.IntegerField(default=0)
    encrypt = models.BooleanField(default=False)
    sign = models.BooleanField(default=False)
    passphrase = models.CharField(max_length=255)
    expire_date = models.DateTimeField(db_index=True)
    default_key = models.BooleanField(default=False)
    created = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'mail_pgp_keys'

    def is_expired(self):
        return self.expire_date < timezone.now()

    def serialize_detail(self):
        tz = pytz.timezone('Asia/Bangkok')
        expire_date = self.expire_date.astimezone(tz)
        created_date = self.created.astimezone(tz)
        
        return {
            'key_id': self.key_id,
            'private_key': getattr(self, 'private_key', None),
            'public_key': getattr(self, 'public_key', None),
            'key_size': getattr(self, 'key_size', None),
            'encrypt': getattr(self, 'encrypt', None),
            'sign': getattr(self, 'sign', None),
            'passphrase': getattr(self, 'passphrase', None),
            'expire_date': expire_date.strftime('%b %d %Y, %I:%M %p'),
            'default_key': self.default_key,
            'created': created_date.strftime('%b %d %Y, %I:%M %p')
        }
        
    def serialize_public(self):
        tz = pytz.timezone('Asia/Bangkok')
        expire_date = self.expire_date.astimezone(tz)
        created_date = self.created.astimezone(tz)
        
        return {
            'key_id': self.key_id,
            'key_size': getattr(self, 'key_size', None),
            'encrypt': getattr(self, 'encrypt', None),
            'sign': getattr(self, 'sign', None),
            'expire_date': expire_date.strftime('%b %d %Y, %I:%M %p'),
            'default_key': self.default_key,
            'created': created_date.strftime('%b %d %Y, %I:%M %p')
        }
        
        
class ReceivedPublicKey(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='public_keys')
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='public_keys_received')
    key_id = models.CharField(max_length=255, db_index=True)
    public_key = models.TextField()
    expire_date = models.DateTimeField(db_index=True)
    
    class Meta:
        db_table = 'mail_received_public_keys'
        unique_together = ('user', 'owner')
        indexes = [
            models.Index(fields=['user', 'owner']),  # Composite index
        ]
    
    def is_expired(self):
        return self.expire_date < timezone.now()
    
    def serialize_detail(self):
        return {
            'owner_first_name': self.owner.first_name,
            'owner_last_name': self.owner.last_name,
            'owner_email': self.owner.email,
            'key_id': self.key_id,
            'public_key': self.public_key,
            'expire_date': self.expire_date.strftime('%b %d %Y, %I:%M %p')
        }
    
    def serialize_public(self):
        return {
            'owner_first_name': self.owner.first_name,
            'owner_last_name': self.owner.last_name,
            'owner_email': self.owner.email,
            'key_id': self.key_id,
            'expire_date': self.expire_date.strftime('%b %d %Y, %I:%M %p')
        }
        
        
class EmailPGPKey(models.Model):
    email = models.ForeignKey(Email, on_delete=models.CASCADE, related_name='public_keys')
    recipient_public_key = models.ForeignKey(ReceivedPublicKey, on_delete=models.CASCADE, related_name='emails', null=True)
    sender_public_key = models.ForeignKey(PGPKey, on_delete=models.CASCADE, related_name='emails', null=True)
    
    class Meta:
        db_table = 'mail_email_pgp_keys'
        indexes = [
            models.Index(fields=['email', 'recipient_public_key']),  # Composite index
        ]
    
    def serialize(self):
        return {
            'email': self.email.id,
            'recipient_public_key': self.recipient_public_key.public_key,
            'sender_public_key': self.sender_public_key.public_key
        }