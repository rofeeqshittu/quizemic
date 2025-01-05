# quiz/admin/mixins.py

from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.shortcuts import redirect
from django.urls import reverse_lazy

class AdminRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    """
    Mixin to ensure only admin users can access admin views
    """
    login_url = reverse_lazy('login')
    
    def test_func(self):
        return self.request.user.is_staff or self.request.user.is_superuser
    
    def handle_no_permission(self):
        if not self.request.user.is_authenticated:
            return super().handle_no_permission()
        return redirect('home')

class AdminViewMixin(AdminRequiredMixin):
    """
    Base mixin for all admin views with common functionality
    """
    template_name_suffix = '_form'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['is_admin_view'] = True
        return context
