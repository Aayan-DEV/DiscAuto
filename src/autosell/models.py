from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

# First we define a model named "AutoSell" that recieves data from Django's Model Class. 
class AutoSell(models.Model):
    # A relationship to the user model, that makes it so that each instance is linked to a user. 
    user = models.ForeignKey(User, on_delete=models.CASCADE) 
    # Image fields which store the banner and the profile image to the directory. 
    banner = models.ImageField(upload_to='banners/')
    profile_picture = models.ImageField(upload_to='profiles/')
    # Character fields that store the name and title with a max length of 100 characters. 
    name = models.CharField(max_length=100)
    title = models.CharField(max_length=100)
    # Email field that stores the user's email address. 
    email = models.EmailField()
    # URL fields that store the user's Instagram and TikTok links.
    instagram_link = models.URLField(max_length=200)
    tiktok_link = models.URLField(max_length=200)
    # CharField that stores the user's custom link. It should be unique and a maximum length of 200 characters.
    custom_link = models.CharField(max_length=200, unique=True)
    # This is a standard procedure in django that returns a string representation of the model instance,
    # for easy identification in the django admin. 
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
