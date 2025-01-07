# quiz/admin/views/user.py

from django.views.generic import ListView, DetailView, TemplateView, CreateView, UpdateView, DeleteView
from django.contrib.messages.views import SuccessMessageMixin
from django.urls import reverse_lazy
from django.contrib import messages
from django.shortcuts import redirect
from django.views import View
from django.contrib.auth import get_user_model
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.db.models import Count, Avg
from quiz.models import QuizResult
from ..mixins import AdminRequiredMixin

User = get_user_model()

class UserListView(AdminRequiredMixin, ListView):
    model = User
    template_name = 'admin/quiz/user_list.html'
    context_object_name = 'users'
    paginate_by = 10

    def get_queryset(self):
        queryset = User.objects.annotate(
            quiz_count=Count('quizresult'),
            avg_score=Avg('quizresult__score')
        )
        search_query = self.request.GET.get('search')
        if search_query:
            queryset = queryset.filter(username__icontains=search_query)
        return queryset.order_by('-date_joined')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['can_add_user'] = self.request.user.has_perm('auth.add_user')
        context['can_delete_user'] = self.request.user.has_perm('auth.delete_user')
        return context

class UserCreateView(AdminRequiredMixin, SuccessMessageMixin, CreateView):
    model = User
    template_name = 'admin/quiz/user_form.html'
    fields = ['username', 'email', 'password', 'is_staff', 'is_active']
    success_url = reverse_lazy('quiz_admin:user_list')
    success_message = "User %(username)s was created successfully"

    def form_valid(self, form):
        user = form.save(commit=False)
        user.set_password(form.cleaned_data['password'])
        return super().form_valid(form)

class UserUpdateView(AdminRequiredMixin, SuccessMessageMixin, UpdateView):
    model = User
    template_name = 'admin/quiz/user_form.html'
    fields = ['username', 'email', 'is_staff', 'is_active']
    success_url = reverse_lazy('quiz_admin:user_list')
    success_message = "User %(username)s was updated successfully"

class UserDeleteView(AdminRequiredMixin, DeleteView):
    model = User
    template_name = 'admin/quiz/user_confirm_delete.html'
    success_url = reverse_lazy('quiz_admin:user_list')
    success_message = "User was deleted successfully"

    def delete(self, request, *args, **kwargs):
        messages.success(self.request, self.success_message)
        return super().delete(request, *args, **kwargs)

class UserToggleActiveView(AdminRequiredMixin, View):
    def post(self, request, pk):
        user = User.objects.get(pk=pk)
        user.is_active = not user.is_active
        user.save()
        status = 'activated' if user.is_active else 'deactivated'
        messages.success(request, f'User {user.username} has been {status}')
        return redirect('quiz_admin:user_list')

class UserDetailView(AdminRequiredMixin, DetailView):
    model = User
    template_name = 'admin/quiz/user_detail.html'
    context_object_name = 'user_profile'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.get_object()
        context['quiz_results'] = QuizResult.objects.filter(user=user).select_related('quiz')
        return context

class UserActivityView(AdminRequiredMixin, TemplateView):
    template_name = 'admin/quiz/user_activity.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = User.objects.get(pk=self.kwargs['pk'])
        context['user'] = user
        context['recent_activity'] = QuizResult.objects.filter(user=user).order_by('-completed_at')[:10]
        return context
