# users/urls.py

from django.urls import path
from django.contrib.auth import views as auth_views
from . import views
from .forms import CustomAuthenticationForm, CustomPasswordResetForm, CustomSetPasswordForm


class CustomLoginView(auth_views.LoginView):
    template_name = 'users/login.html'
    authentication_form = CustomAuthenticationForm
    redirect_authenticated_user = True

    def get_success_url(self):
        next_url = self.request.GET.get('next')
        if next_url and 'quiz-admin' in next_url and self.request.user.is_staff:
            return next_url
        return super().get_success_url()

urlpatterns = [
    path('register/', views.register, name='register'),
    path('profile/', views.profile, name='profile'),
    #path('login/', auth_views.LoginView.as_view(
        #template_name='users/login.html',
        #authentication_form=CustomAuthenticationForm
    #), name='login'),
    path('login/', CustomLoginView.as_view(), name='login'),  # New
    path('logout/', auth_views.LogoutView.as_view(next_page='home'), name='logout'),
    # ... My existing urls above ...
    path('password-reset/',
         auth_views.PasswordResetView.as_view(
             template_name='users/password_reset.html',
             form_class=CustomPasswordResetForm
         ),
         name='password_reset'),
    path('password-reset/done/',
         auth_views.PasswordResetDoneView.as_view(
             template_name='users/password_reset_done.html'
         ),
         name='password_reset_done'),
    path('password-reset-confirm/<uidb64>/<token>/',
         auth_views.PasswordResetConfirmView.as_view(
             template_name='users/password_reset_confirm.html',
             form_class=CustomSetPasswordForm
         ),
         name='password_reset_confirm'),
    path('password-reset-complete/',
         auth_views.PasswordResetCompleteView.as_view(
             template_name='users/password_reset_complete.html'
         ),
         name='password_reset_complete'),


    path('update-profile/', views.update_profile, name='update_profile'),


    ]
