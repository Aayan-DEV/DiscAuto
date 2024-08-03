from django.shortcuts import render

# Create your views here.
def auths(request):
    return render(request, 'features/auths/auths.html', {})