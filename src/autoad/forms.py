from django import forms 

# First DataForm is defined that inherits from Django's "forms.Form", meaning it gets data from Django's forms.Form
class DataForm(forms.Form):
    # The integer field is created to enter the channel ID, which is set to required=True, the label attribute is used to specify the text that will be displayed. 
    channel_id = forms.IntegerField(required=True, label='Channel ID')
  