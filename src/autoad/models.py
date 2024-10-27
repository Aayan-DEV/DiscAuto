from django.db import models 
from django.contrib.auth.models import User
from django.utils import timezone

# First we define a model named "Channels" that recieves data from Django's Model Class. 
class Channels(models.Model):
    """
    Here a ForignKey relationship is established to the User model, meaning that each channel is associated with a user. 
    The on_delete=models.CASCADE means that if a user is deleted, all the associated channels are also deleted. This is
    important because if a user is deleted their corresponding created channels should not be saved as to clean up, organise and 
    because the user decided to delete their data.  
    The related_name makes it easy to access the related objects in a more readable way.
    For example: a_user.autoad_channels.all() is more understandable. 
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='autoad_channels')
    # A character field is created to store the channel name, with a mximum length of 255 characters. 
    channel_name = models.CharField(max_length=255)
    # A character field is created to store the channel ID, with a maximum length of 255 characters. "unique=True" is used to make sure that the ID is unique.
    channel_id = models.CharField(max_length=255, unique=True)
    # The hour, minute and second fields are Integer fields, the default value in each case is 0, to make sure if the user doesnt enter any number, it should be 0. 
    hours = models.IntegerField(default=0)
    minutes = models.IntegerField(default=0)
    seconds = models.IntegerField(default=0)
    # The DateTime field is used to store the start time of the channel, and the default value is set to the current time when the timer first is created and confirmed. 
    start_time = models.DateTimeField(default=timezone.now)

    ad_count = models.IntegerField(default=0)

    # The __str__(self) method is usual in Django, used to return a human readable string representation of the model instance.
    def __str__(self):
        return f"{self.channel_name} - {self.channel_id}"
    # This method is used to calculate and return the total number of seconds from the hour, minutes and seconds. Used to have 1 value, instead of 3.
    def get_total_seconds(self):
        return self.hours * 3600 + self.minutes * 60 + self.seconds
    
    class Meta:
        # 'verbose_name_plural' specifies a more human-readable name for the model in the Django admin.
        verbose_name_plural = "Channels"
 