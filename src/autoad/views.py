# All imports: 
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from .models import Channels
from django.utils import timezone
from django.core.mail import send_mail
from django.views.decorators.http import require_POST
from dotenv import load_dotenv
import os
from django.utils import timezone
from django.db.models import F
 
# Auto_ad function made to handle the autoad feature. 
@login_required
def auto_ad(request):
    """
    First see if the method is POST, this is when the 
    create button sends a request to the website, we 
    check to see if that request is POST or not.

    """
    if request.method == 'POST':
        #Then get all the data from the form.
        channel_name = request.POST.get('channel_name')
        channel_id = request.POST.get('channel_id')
        hours = int(request.POST.get('hours'))
        minutes = int(request.POST.get('minutes'))
        seconds = int(request.POST.get('seconds'))
        """
        
        We imported "Channels", which is in the database, and it 
        has the details of the channel entered by the user. 
        We first check if the required fields are present or not, (Channel name and ID).

        """
        if channel_name and channel_id:
            #Then we save all the data gotten from the Form, in the Djando Database. 
            #The .save() function in django updates the table.
            new_channel = Channels(
                user=request.user,
                channel_name=channel_name,
                channel_id=channel_id,
                hours=hours,
                minutes=minutes,
                seconds=seconds,
                start_time=timezone.now() 
            )
            #Saves the new channel in the database.
            new_channel.save()

            #This is the success response given once a channel and timer have been saved successfully. 
            return JsonResponse({'success': True, 'message': 'Channel and timer saved successfully!'})

        #This is the Error message given when a field is empty and the add button is pressed.
        return JsonResponse({'success': False, 'message': 'Missing required fields!'})

    #Get only the objects from the database, corresponding to channels and the current user, and set is equal to channels.
    channels = Channels.objects.filter(user=request.user)
    #Here we are initializing an empty list, to store all the channel data.
    channel_data = []

    #Now we are going to loop through each channel object.
    for channel in channels:
        """
        The .get_total_seconds() method has been defined in models.py. It converts hours and minutes 
        to seconds, then it adds the hours (in seconds), minutes (in seconds) and seconds. This way
        it is much easier to compare time, with only 1 value, rather than 3.
        """
        total_seconds = channel.get_total_seconds()
        """
        Here we calculate the elapsed time, we get the current time, then we subtract the start time, 
        And then we get the total amount of time, in seconds using total_seconds().
        """
        time_elapsed = (timezone.now() - channel.start_time).total_seconds()
        """
        Now we get the remaining time, where we subtract the time elapsed from the total seconds. 
        The max function is used to get maximum of the values (0, total_seconds - time_elapsed), to
        ensure that the remaining time is never negative. The 0 is used as the lower bound for
        the remaining time, so max will chose the bigger value, or if the value is less than 0, 
        it will choose 0. 
        """
        remaining_time = max(0, total_seconds - time_elapsed)  

        #Now we just convert the remaining time into hours, minutes and seconds.
        hours = int(remaining_time // 3600)
        minutes = int((remaining_time % 3600) // 60)
        seconds = int(remaining_time % 60)

        #Here we append the channel data to the list.
        channel_data.append({
            'channel_name': channel.channel_name,
            'channel_id': channel.channel_id,
            'hours': hours,
            'minutes': minutes,
            'seconds': seconds,
            'remaining_time': remaining_time
        })
    """
    Here we render the auto-ad template with the channel data. The reason
    why channels has been provided is because it is going to help access
    all the data for the channel in the template. Providing it here makes 
    it so in the auto-ad.html template, i can access the channel data.
    """
    return render(request, 'features/auto-ad/auto-ad.html', {
        'channels': channel_data 
    })

#This function is used to delete a channel from the database, after it has been deleted in the template.
#It says login required, so that a unknown user can't randomly delete stuff.
#Require POST because it only should work if a POST method has been called by the template. 
@login_required
@require_POST
def delete_channel(request):
    #First of all we get the channel ID from the POST request, to identify what is being deleted. 
    channel_id = request.POST.get('channel_id')
    """
    Then we can check if the channel ID is provided, if yes continue, if not then give an error. This 
    won't really happen as channel ID will always be given and is being checked before, but just incase
    there is any error in the database. 
    """
    if channel_id:
        try:
            #First we try to get the channel with the channel ID provided in the POST. 
            # All channel ID's are unique
            channel = Channels.objects.get(channel_id=channel_id)
            #Then we delete the channel from the database, and it is also deleted on the frontend. 
            channel.delete()
            #A success response is returned if the channel was deleted successfully. 
            return JsonResponse({'success': True, 'message': 'Channel deleted successfully!'})
        except Channels.DoesNotExist:
            """
            If a channel does not exist then a channel not found message would be shown. Again, 
            it probalby wont happen, but just incase anything goes wrong, there would be a 
            messsage to explain.
            """
            return JsonResponse({'success': False, 'message': 'Channel not found!'})
    return JsonResponse({'success': False, 'message': 'Missing channel ID!'})

#This is a function that sends an email to the user after a timer expires. To remind them that the timer has expired and they have to place and ad. 
@login_required
@require_POST
def send_timer_expiry_email(request):
    # First we get the channel name and the ID from the request (a request to send the email), to put them inside the email. 
    channel_name = request.POST.get('channel_name')
    channel_id = request.POST.get('channel_id')

    # We then double check that the channel name and id are provided.
    if channel_name and channel_id:
        try:
            # First we check if the channel still exists before proceeding, the user could have deleted the channel
            # It continues if it exists, and does nothing if it doesnt.
            Channels.objects.get(channel_id=channel_id)
        except Channels.DoesNotExist:
            # If the channel does not exist, do nothing (no response, no email sent)
            return

        # It then gets the email of the currently logged-in user.
        user_email = request.user.email  

        # This is a part to get the email sender, from the .env file.
        if not os.getenv('RAILWAY_ENVIRONMENT'):
            load_dotenv(override=True)
        EMAIL_HOST_USER = os.getenv('EMAIL_HOST_USER')

        """
        It creates a subject line for the email to be sent, and uses the channel name so that the user can identify 
        the channel using the search bar if he has too many ad reminders. 
        """
        subject = f'Timer Expired for Channel: {channel_name}'
        # This creates the body of the email, it gets the user's name to adress the user. 
        message = f'Hi {request.user.username},\n\nThe timer for channel "{channel_name}" (ID: {channel_id}) has expired.\n\nThank you!'
        # The email sent from, uses the environment variable. 
        from_email = EMAIL_HOST_USER  
        # It sends the email:
        send_mail(
            subject,
            message,
            from_email,
            [user_email], # Email of the current user who is logged in, meaning the user who created the timer. 
            fail_silently=False, # If there is an error, it raises an exception instead of failing silently so that we know whats the problem and can solve it.
        )

        return JsonResponse({'success': True, 'message': 'Email sent successfully!'})
        # Returns a JSON response saying that the email was sent successfully.    

    return JsonResponse({'success': False, 'message': 'Missing channel name or ID!'})
    # Returns a JSON response saying the channel name or ID is missing. 

"""
This function below is used to confirm the ad is posted, so that there can be an increment in the number of ad posted for 
a perticular user, so that we can display the number on the dashboard. 
"""
@login_required
def confirm_ad_posted(request, channel_id):
    # First check if the request method is POST
    if request.method == 'POST': 
        try:
            # Check if channel_id is provided in the request, This HAS to be provided, and will 100% be there as without it,
            # the channel Box would not even exist. But just in case there was a problem, there is error checking implemented. 
            if not channel_id:
                return JsonResponse({'success': False, 'message': 'No channel_id provided'}, status=400)
            
            # Then we get the channel Id from the request
            channel = Channels.objects.get(channel_id=channel_id)

            # Becuase each channel id is unique, when we increase the ad count, that 
            # increment always increased the correct ad box's count. 
            # The F() is a great way in Django to reference the field in the database. 
            # The F() modifies and saves the field in a single query and is very efficient. 
            channel.ad_count = F('ad_count') + 1
            channel.save()

            return JsonResponse({'success': True})

        except Channels.DoesNotExist:
            return JsonResponse({'success': False, 'message': 'Channel not found'}, status=404)

        except Exception as e:
            # Log the error for debugging
            print(f"Error: {str(e)}")
            return JsonResponse({'success': False, 'message': str(e)}, status=500)

    # If it's not a POST request, return a 405 Method Not Allowed
    return JsonResponse({'success': False, 'message': 'Invalid request method'}, status=405)
