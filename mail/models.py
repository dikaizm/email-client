from django.contrib.auth.models import AbstractUser
from django.utils import timezone
from django.db import models
import pytz


class User(AbstractUser):
    def __str__(self):
        return f'{self.username}'


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