from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import UserProfile

@login_required
def auths(request):
    profile, created = UserProfile.objects.get_or_create(user=request.user)
    
    if request.method == 'POST':
        profile.pushover_user_key = request.POST.get('pushover_user_key', profile.pushover_user_key)
        profile.paypal_email = request.POST.get('paypal_email', profile.paypal_email)
        profile.btc_wallet = request.POST.get('btc_wallet', profile.btc_wallet)
        profile.ltc_wallet = request.POST.get('ltc_wallet', profile.ltc_wallet)
        profile.sol_wallet = request.POST.get('sol_wallet', profile.sol_wallet)
        profile.eth_wallet = request.POST.get('eth_wallet', profile.eth_wallet)
        profile.usdt_bep20_wallet = request.POST.get('usdt_bep20_wallet', profile.usdt_bep20_wallet)
        profile.usdt_erc20_wallet = request.POST.get('usdt_erc20_wallet', profile.usdt_erc20_wallet)
        profile.usdt_prc20_wallet = request.POST.get('usdt_prc20_wallet', profile.usdt_prc20_wallet)
        profile.usdt_sol_wallet = request.POST.get('usdt_sol_wallet', profile.usdt_sol_wallet)
        profile.usdt_trc20_wallet = request.POST.get('usdt_trc20_wallet', profile.usdt_trc20_wallet)
        
        profile.save()
        messages.success(request, "Your settings have been saved.")
        return redirect('auths')
    
    return render(request, 'features/auths/auths.html', {'profile': profile})
