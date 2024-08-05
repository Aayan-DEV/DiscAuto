from django.db import models
from django.contrib.auth.models import User

class DiscordToken(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    token = models.CharField(max_length=255)
    username = models.CharField(max_length=255, blank=True, null=True)

    class Meta:
        unique_together = ('user', 'token')

    def __str__(self):
        return f"{self.user.username} - {self.username or self.token}"
