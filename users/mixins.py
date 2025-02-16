from django.contrib.auth.mixins import UserPassesTestMixin
from django.shortcuts import redirect
from django.contrib import messages

class AdminRequiredMixin(UserPassesTestMixin):
    def test_func(self):
        return self.request.user.role == 'admin'
    
    def handle_no_permission(self):
        messages.error(self.request, "No tienes permisos para acceder a esta sección.")
        return redirect('dashboard:index')