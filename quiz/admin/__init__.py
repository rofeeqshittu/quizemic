# quiz/admin/__init__.py

from django.contrib.admin import AdminSite
from django.urls import path, include
from django.template.response import TemplateResponse
from django.shortcuts import redirect
from django.contrib.auth.decorators import login_required, user_passes_test

class QuizAdminSite(AdminSite):
    site_header = 'Quiz Admin'
    site_title = 'Quiz Admin Portal'
    index_title = 'Quiz Administration'

    def has_permission(self, request):
        # Check if user is authenticated and is staff
        return request.user.is_authenticated and request.user.is_staff

    def index(self, request):
        if not self.has_permission(request):
            return redirect('login')  # Use your login URL name

        context = {
            'title': 'Quiz Administration',
            'site_title': self.site_title,
            'site_header': self.site_header,
            'has_permission': True,
        }
        return TemplateResponse(request, 'admin/quiz/dashboard.html', context)

admin_site = QuizAdminSite(name='quiz_admin')
