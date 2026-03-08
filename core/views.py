from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.views import LoginView as AuthLoginView
from django.shortcuts import redirect, render


def signup(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, 'Conta criada com sucesso!')
            return redirect('catalog:product_list')
    else:
        form = UserCreationForm()

    return render(request, 'registration/signup.html', {'form': form})


def logout_view(request):
    # Preserva carrinho ao sair
    cart_data = request.session.get('cart')
    coupon_id = request.session.get('coupon_id')
    logout(request)
    if cart_data is not None:
        request.session['cart'] = cart_data
    if coupon_id:
        request.session['coupon_id'] = coupon_id
    request.session.modified = True
    messages.info(request, 'Você saiu da conta.')
    return redirect('catalog:product_list')


class LoginView(AuthLoginView):
    template_name = 'registration/login.html'

    def form_valid(self, form):
        # Guarda carrinho antes do rotation da sessão
        cart_data = self.request.session.get('cart')
        coupon_id = self.request.session.get('coupon_id')
        response = super().form_valid(form)
        if cart_data is not None:
            self.request.session['cart'] = cart_data
        if coupon_id:
            self.request.session['coupon_id'] = coupon_id
        self.request.session.modified = True
        return response
