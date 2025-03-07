from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import UserProfile

@login_required
def auths(request):
    profile, created = UserProfile.objects.get_or_create(user=request.user)
    
    # Define wallet fields for template
    wallet_fields = [
        ('BTC Wallet', 'btc_wallet', profile.btc_wallet),
        ('LTC Wallet', 'ltc_wallet', profile.ltc_wallet),
        ('SOL Wallet', 'sol_wallet', profile.sol_wallet),
        ('ETH Wallet', 'eth_wallet', profile.eth_wallet),
        ('USDT (BEP20)', 'usdt_bep20_wallet', profile.usdt_bep20_wallet),
        ('USDT (ERC20)', 'usdt_erc20_wallet', profile.usdt_erc20_wallet),
        ('USDT (PRC20)', 'usdt_prc20_wallet', profile.usdt_prc20_wallet),
        ('USDT (SOL)', 'usdt_sol_wallet', profile.usdt_sol_wallet),
        ('USDT (TRC20)', 'usdt_trc20_wallet', profile.usdt_trc20_wallet),
    ]

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
    
    return render(request, 'features/auths/auths.html', {
        'profile': profile,
        'wallet_fields': wallet_fields,
    })


'''
Citations:
("Writing Your First Django App") -> 27
(JcKelley) -> 13 - 23
(Saleh, Ali)-> 9
'''