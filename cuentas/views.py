from django.shortcuts import render, redirect
from django.contrib.auth import login
from .forms import ClienteRegistroForm, NegocioRegistroForm
from django.contrib.auth.views import LoginView


def registro_cliente(request):
    if request.method == 'POST':
        form = ClienteRegistroForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('home')  # redirige donde tú quieras
    else:
        form = ClienteRegistroForm()
    return render(request, 'cuentas/registro_cliente.html', {'form': form})


def registro_negocio(request):
    if request.method == 'POST':
        form = NegocioRegistroForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('home')
    else:
        form = NegocioRegistroForm()
    return render(request, 'cuentas/registro_negocio.html', {'form': form})


class LoginUsuario(LoginView):
    template_name = 'cuentas/login.html'



