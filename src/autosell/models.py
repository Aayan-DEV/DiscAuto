from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

# First we define a model named "AutoSell" that recieves data from Django's Model Class. 
class AutoSell(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    banner = models.ImageField(upload_to='banners/', max_length=500)  # Increase max_length
    profile_picture = models.ImageField(upload_to='profiles/', max_length=500)  # Increase max_length
    name = models.CharField(max_length=200)
    title = models.CharField(max_length=200)
    email = models.EmailField()
    instagram_link = models.URLField(max_length=200)
    tiktok_link = models.URLField(max_length=200)
    custom_link = models.CharField(max_length=200, unique=True)

    def __str__(self):
        return self.name

# We define another model named "AutoSellView" that recieves data from Django's Model Class.
class AutoSellView(models.Model):
    # A ForeginKey, that makes it so that each instance is linked to a AutoSell.
    autosell = models.ForeignKey(AutoSell, on_delete=models.CASCADE)
    # DateField that stores the date when the view was made. It defaults to the current date and time.
    view_date = models.DateField(default=timezone.now)
    # Again, it is a standard procedure in django that returns a string representation of the model instance,
    # for easy identification in the django admin. 
    def __str__(self):
        return f"View on {self.view_date} for {self.autosell.name}"
