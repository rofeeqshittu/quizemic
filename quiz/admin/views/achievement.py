# /quiz/admin/views/achievement.py

from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from django.contrib import messages
from django.db import models  # Add this import
from django.db.models import Count, F, Q, OuterRef, Subquery
from quiz.models import Achievement, UserAchievement
from ..mixins import AdminRequiredMixin
from django.db.models import Q, Count
from quiz.analytics import AchievementTracker

class AchievementListView(AdminRequiredMixin, ListView):
    model = Achievement
    template_name = 'admin/quiz/achievement_list.html'
    context_object_name = 'achievements'
    paginate_by = 10

    def get_queryset(self):
        # Using subquery to count related UserAchievements
        queryset = Achievement.objects.annotate(
            earned_count_annotation=Subquery(
                UserAchievement.objects.filter(
                    achievement_key=OuterRef('key')
                ).values('achievement_key')
                .annotate(count=Count('id'))
                .values('count')
            )
        )
        
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(
                Q(title__icontains=search) |
                Q(description__icontains=search)
            )
        return queryset.order_by('-created_at')    

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Get tracker achievements and their earned counts
        context['tracker_achievements'] = [
            {
                'key': key,
                'data': achievement_data,
                'earned_count': UserAchievement.objects.filter(
                    achievement_key=key
                ).count()
            }
            for key, achievement_data in AchievementTracker.ACHIEVEMENTS.items()
        ]
        return context

class AchievementCreateView(AdminRequiredMixin, CreateView):
    model = Achievement
    template_name = 'admin/quiz/achievement_form.html'
    fields = ['key', 'title', 'description', 'icon']
    success_url = reverse_lazy('quiz_admin:achievement_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['available_achievements'] = {
            key: data for key, data in AchievementTracker.ACHIEVEMENTS.items()
            if not Achievement.objects.filter(key=key).exists()
        }
        return context

    def form_valid(self, form):
        key = form.cleaned_data['key']
        if key in AchievementTracker.ACHIEVEMENTS:
            tracker_achievement = AchievementTracker.ACHIEVEMENTS[key]
            form.instance.title = tracker_achievement['title']
            form.instance.description = tracker_achievement['description']
            form.instance.icon = tracker_achievement['icon']
            messages.success(self.request, 'Achievement created successfully!')
            return super().form_valid(form)
        else:
            form.add_error('key', 'Invalid achievement key')
            return super().form_invalid(form)

class AchievementUpdateView(AdminRequiredMixin, UpdateView):
    model = Achievement
    template_name = 'admin/quiz/achievement_form.html'
    fields = ['key', 'title', 'description', 'icon']
    success_url = reverse_lazy('quiz_admin:achievement_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['available_achievements'] = AchievementTracker.ACHIEVEMENTS
        return context

    def form_valid(self, form):
        messages.success(self.request, 'Achievement updated successfully!')
        return super().form_valid(form)

class AchievementDeleteView(AdminRequiredMixin, DeleteView):
    model = Achievement
    template_name = 'admin/quiz/achievement_confirm_delete.html'
    success_url = reverse_lazy('quiz_admin:achievement_list')

    def delete(self, request, *args, **kwargs):
        messages.success(request, 'Achievement deleted successfully!')
        return super().delete(request, *args, **kwargs)
