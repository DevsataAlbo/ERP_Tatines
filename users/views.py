from django.shortcuts import render
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.contrib.auth.views import LoginView as AuthLoginView
from django.contrib.auth.views import LogoutView as AuthLogoutView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from .models import User
from django.contrib.auth.hashers import make_password
from django.contrib import messages
from .mixins import AdminRequiredMixin
from django.views.generic.detail import DetailView
from .models import User

class LoginView(AuthLoginView):
    template_name = 'users/login.html'
    redirect_authenticated_user = True
    
    def get_success_url(self):
        return reverse_lazy('dashboard:index')

class LogoutView(AuthLogoutView):
    next_page = 'users:login'

class ProfileView(LoginRequiredMixin, UpdateView):
    model = User
    template_name = 'users/profile.html'
    fields = ['username', 'email', 'first_name', 'last_name', 'phone', 'address', 'image']
    success_url = reverse_lazy('users:profile')
    
    def get_object(self):
        return self.request.user
    
    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        # Añadir clases a los campos
        for field in form.fields:
            form.fields[field].widget.attrs.update({
                'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500'
            })
        return form

    def form_valid(self, form):
        messages.success(self.request, 'Perfil actualizado exitosamente.')
        return super().form_valid(form)

class UserListView(LoginRequiredMixin, AdminRequiredMixin, ListView):
    model = User
    template_name = 'users/list.html'
    context_object_name = 'users'

    def get_queryset(self):
        return User.objects.all().order_by('-date_joined')

class UserCreateView(LoginRequiredMixin, AdminRequiredMixin, CreateView):
    model = User
    template_name = 'users/form.html'
    fields = ['username', 'email', 'password', 'first_name', 'last_name', 'role']
    success_url = reverse_lazy('users:list')
    
    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        # Añadir clases a los campos
        for field in form.fields:
            form.fields[field].widget.attrs.update({
                'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500'
            })
        # Cambiar el widget de password a PasswordInput
        form.fields['password'].widget.input_type = 'password'
        return form
    
    def form_valid(self, form):
        # Hashear la contraseña antes de guardar
        form.instance.password = make_password(form.cleaned_data['password'])
        messages.success(self.request, 'Usuario creado exitosamente.')
        return super().form_valid(form)

class UserUpdateView(LoginRequiredMixin, AdminRequiredMixin, UpdateView):
    model = User
    template_name = 'users/form.html'
    fields = ['username', 'email', 'first_name', 'last_name', 'role', 'is_active']
    success_url = reverse_lazy('users:list')
    
    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        for field in form.fields:
            form.fields[field].widget.attrs.update({
                'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500'
            })
        return form
    
    def form_valid(self, form):
        messages.success(self.request, 'Usuario actualizado exitosamente.')
        return super().form_valid(form)

class UserDeleteView(LoginRequiredMixin, AdminRequiredMixin, DeleteView):
    model = User
    template_name = 'users/delete.html'
    success_url = reverse_lazy('users:list')


