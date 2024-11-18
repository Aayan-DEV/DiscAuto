from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DefaultUserAdmin
from django.contrib.auth.models import User
from .models import UserProfile

# Here we define an inline admin interface for the UserProfile model to show an external model inside another interface.
class UserProfileInline(admin.StackedInline): 
    # This is the model that will be displayed.
    model = UserProfile 
    # This field will be read-only in the interface.
    can_delete = False
    # The name would be "Profile"
    verbose_name_plural = 'Profile'

# Here we extend the default UserAdmin to also inclide the UserProfileInline
class UserAdmin(DefaultUserAdmin):
    # Add UserProfile as an inline in the User admin interface
    inlines = (UserProfileInline,)  

# Fist we unregister the default User admin, so it can be re-registered with changes
admin.site.unregister(User) 
# Then we register the modified UserAdmin that includes the UserProfile inline
admin.site.register(User, UserAdmin) 


'''
Citations: 
("The Django Admin") -> 7-13 , 22-24 
("Document How to Extend UserAdmin") -> 16 - 17
'''
