# payment_providers/views.py
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from .models import PaymentProvider

class PaymentProviderListView(LoginRequiredMixin, ListView):
    model = PaymentProvider
    template_name = 'payment_providers/list.html'
    context_object_name = 'providers'

class PaymentProviderCreateView(LoginRequiredMixin, CreateView):
    model = PaymentProvider
    template_name = 'payment_providers/form.html'
    fields = '__all__'
    success_url = reverse_lazy('payment_providers:list')

class PaymentProviderUpdateView(LoginRequiredMixin, UpdateView):
    model = PaymentProvider
    template_name = 'payment_providers/form.html'
    fields = '__all__'
    success_url = reverse_lazy('payment_providers:list')

class PaymentProviderDeleteView(LoginRequiredMixin, DeleteView):
    model = PaymentProvider
    template_name = 'payment_providers/delete.html'
    success_url = reverse_lazy('payment_providers:list')