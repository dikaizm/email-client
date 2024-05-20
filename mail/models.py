from django.contrib.auth.models import AbstractUser
from django.utils import timezone
from django.db import models


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

    def serialize(self):
        return {
            'id': self.id,
            'sender': self.sender.email,
            'recipients': [user.email for user in self.recipients.all()],
            'subject': self.subject,
            'body': self.body,
            'timestamp': self.timestamp.strftime('%b %d %Y, %I:%M %p'),
            'read': self.read,
            'archived': self.archived,
            'encrypted': self.encrypted
        }


class PGPKey(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='pgp_keys')
    private_key = models.TextField()
    public_key = models.TextField()
    passphrase = models.CharField(max_length=255)
    expire_date = models.DateTimeField(db_index=True)
    created = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'mail_pgp_keys'

    def is_expired(self):
        return self.expire_date < timezone.now()

    def serialize(self):
        return {
            'private_key': self.private_key,
            'public_key': self.public_key,
            'passphrase': self.passphrase,
            'expire_date': self.expire_date.strftime('%b %d %Y, %I:%M %p'),
            'created': self.created.strftime('%b %d %Y, %I:%M %p')
        }
        
        
class UserPublicKey(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='public_keys')
    recipient = models.ForeignKey(User, on_delete=models.CASCADE, related_name='public_keys_received')
    public_key = models.TextField()
    expire_date = models.DateTimeField(db_index=True)
    
    class Meta:
        db_table = 'mail_user_public_keys'
        unique_together = ('user', 'recipient')
        indexes = [
            models.Index(fields=['user', 'recipient']),  # Composite index
        ]
    
    def is_expired(self):
        return self.expire_date < timezone.now()
    
    def serialize(self):
        return {
            'user': self.user.email,
            'recipient': self.recipient.email,
            'public_key': self.public_key,
            'expire_date': self.expire_date.strftime('%b %d %Y, %I:%M %p')
        }
        
        
class EmailPublicKey(models.Model):
    email = models.ForeignKey(Email, on_delete=models.CASCADE, related_name='public_keys')
    user_public_key = models.ForeignKey(UserPublicKey, on_delete=models.CASCADE, related_name='emails')
    
    class Meta:
        db_table = 'mail_email_public_keys'
        indexes = [
            models.Index(fields=['email', 'user_public_key']),  # Composite index
        ]
    
    def serialize(self):
        return {
            'email': self.email.id,
            'user_public_key': self.user_public_key.id
        }