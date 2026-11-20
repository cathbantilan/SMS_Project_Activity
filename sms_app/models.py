from django.db import models

# Create your models here.
class SMSLog(models.Model):
    recipient = models.CharField(max_length=20)
    message = models.TextField()
    status = models.CharField(max_length=50)
    provider_sid = models.CharField(max_length=64, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.recipient} - {self.status}"

class IncomingSMS(models.Model):
    sender = models.CharField(max_length=20)
    message = models.TextField()
    provider_id = models.CharField(max_length=64, unique=True)
    received_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.sender} - {self.message[:25]}"