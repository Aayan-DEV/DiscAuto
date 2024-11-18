from django.db import models
from django.contrib.auth.models import User

# First we define a model named "ColdDM" that recieves data from Django's Model Class. 
class ColdDM(models.Model):
    # 'username' represents the username of the person the DM was sent to.
    username = models.CharField(max_length=150)
    # 'user_id' represents the Discord ID of the person who received the cold DM.
    user_id = models.CharField(max_length=150)
    # 'note' allows the user to put any other info about the DM.
    # It can be left blank.
    note = models.TextField(blank=True, null=True)
    # 'saved_by' links this ColdDM to the user who saved the DM. 
    # This creates a foreign key relationship with Django's built-in User model.
    # 'on_delete=models.CASCADE' means if the user is deleted, all their ColdDM records are deleted too.
    # 'related_name' allows reverse lookup of ColdDMs for each user as 'user.cold_dms'. If we do not 
    # use this, django will make a default one. 
    saved_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='cold_dms')
    # 'created_at' automatically stores the timestamp when a ColdDM record is created. This is important
    # for showing the +1 created at the right date on the dashboard. 
    created_at = models.DateTimeField(auto_now_add=True)  

    def __str__(self):
        # This method provides a human-readable representation of the ColdDM instance, 
        # showing the username of the person who got the DM and who saved the DM.
        return f'{self.username} (saved by {self.saved_by})'

# Next we define a model named "UserColdDMStats" that recieves data from Django's Model Class. 
# This model keeps track of statistics for each user (the total number of Cold DMs posted).
class UserColdDMStats(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='cold_dm_stats')
    # 'user' links each User to their cold DM stats using a one-to-one relationship.
    # Each user can have only one stats record.
    # 'on_delete=models.CASCADE' means if the user is deleted, the stats record is also deleted.
    # 'related_name' allows reverse lookup of the stats.

    total_cold_dms_posted = models.IntegerField(default=0)
    # 'total_cold_dms_posted' stores the total number of cold DMs posted by the user.
    # This is an integer field with a default value of 0.

    def __str__(self):
        # Provides a readable string representation of the user's cold DM stats.
        return f'{self.user.username} - Cold DMs Posted: {self.total_cold_dms_posted}'

    class Meta:
        # 'verbose_name_plural' specifies a more human-readable name for the model in the Django admin.
        verbose_name_plural = "User Cold DM Stats"


"""
Citations:
("Models") -> Lines 5 - 47
"""