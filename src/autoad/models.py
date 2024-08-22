from django.db import models
from django.contrib.auth.models import User

class AutoAdUser(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    username = models.CharField(max_length=255)

    def __str__(self):
        return self.username

class AutoAdConfig(models.Model):
    user = models.ForeignKey(AutoAdUser, related_name='configs', on_delete=models.CASCADE)
    universal_message = models.TextField(blank=True)

    def __str__(self):
        return f"Bot {self.id}"

class AutoAdDetail(models.Model):
    config = models.ForeignKey(AutoAdConfig, related_name='details', on_delete=models.CASCADE)
    channel_id = models.BigIntegerField()
    usernames = models.CharField(max_length=255)
    slowmode_duration = models.IntegerField()
    channel_name = models.CharField(max_length=255)
    server_name = models.CharField(max_length=255)
    universal_message = models.TextField(blank=True)
    custom_message = models.TextField(blank=True)
    bot_running = models.BooleanField(default=False)
    token = models.CharField(max_length=255)
    box_number = models.IntegerField()

    def __str__(self):
        return f"Bot {self.box_number} for {self.config.user.username}"
