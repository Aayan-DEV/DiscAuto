from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from .models import ColdDM, UserColdDMStats
from django.contrib.auth.decorators import login_required
from django.db.models import F
from django.contrib import messages
from django.db import DataError

@login_required 
def cold_dm_view(request):
    if request.method == 'POST':  
        # Get the 'username' from the form data and save it.
        username = request.POST.get('username')  
         # Get the 'user_id' from the form data and save it.
        user_id = request.POST.get('user_id')   
        # Get the 'note' (optional field) and save it. 
        note = request.POST.get('note')         

        # Make sure that both username and user_id are provided as they are required. 
        if username and user_id:  
            try:
                # Here we create a new ColdDM entry and automatically set the logged-in user as 'saved_by'
                ColdDM.objects.create(username=username, user_id=user_id, note=note, saved_by=request.user)
                # We also increment the total number of Cold DMs posted by the user
                stats, created = UserColdDMStats.objects.get_or_create(user=request.user)
                # Use F method to increment the count directly in the database
                stats.total_cold_dms_posted = F('total_cold_dms_posted') + 1
                stats.save()
                messages.success(request, "Cold DM successfully saved!")
            except DataError:
                if len(username) >= 151:
                # Add an error message if the data is too long
                    messages.error(request, "Username field should be less than 150 characters!")
                elif len(user_id) >= 151:
                # Add an error message if the data is too long
                    messages.error(request, "User ID field should be less than 150 characters!")
            except Exception as e:
                # Generic fallback error message
                messages.error(request, f"An unexpected error occurred: {str(e)}")
            return JsonResponse({'success': True})
            # Return success response in JSON format
            return JsonResponse({'success': True})
        # Return error response if required fields are missing
        return JsonResponse({'success': False, 'message': 'Invalid input'})

    # If not a POST request, retrieve all ColdDM entries saved by the current user
    # This is useful as we will be listing all the entries made by the user visually. 
    cold_dm_list = ColdDM.objects.filter(saved_by=request.user)
    # Render the cold-dm.html template and pass the list of Cold DMs to the template
    return render(request, "features/cold-dm/cold-dm.html", {'cold_dm_list': cold_dm_list})


@login_required 
def delete_cold_dm(request, user_id):
    # First we find the ColdDM entry by user_id and ensure it was saved by the current user
    cold_dm_entry = get_object_or_404(ColdDM, user_id=user_id, saved_by=request.user)
    # Delete the ColdDM entry
    cold_dm_entry.delete() 

    # Get the user's stats and decrement the Cold DMs posted count if greater than 0
    stats = UserColdDMStats.objects.get(user=request.user)
    if stats.total_cold_dms_posted > 0:
        stats.total_cold_dms_posted = F('total_cold_dms_posted') - 1 
        stats.save()

    # Return success response in JSON format
    return JsonResponse({'success': True})


@login_required  
def update_cold_dm(request, user_id):
    # Find the ColdDM entry by user_id and ensure it was saved by the current user
    cold_dm_entry = get_object_or_404(ColdDM, user_id=user_id, saved_by=request.user)
    
    if request.method == 'POST':  
        # Get the 'note' from the form data
        note = request.POST.get('note')  
        # Make sure that the note is not empty
        if note:  
            # Update the note for the ColdDM entry
            cold_dm_entry.note = note  
            # Save the changes
            cold_dm_entry.save() 
            # Return success response in JSON format
            return JsonResponse({'success': True})
        # Return error response if the note input is invalid
        return JsonResponse({'success': False, 'message': 'Invalid note input'})

    # Return error response if the request method is not POST
    return JsonResponse({'success': False, 'message': 'Invalid request method'})



