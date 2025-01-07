# quiz/admin/views/dashboard.py

from django.views.generic import TemplateView, FormView
from django.urls import reverse_lazy
from django.contrib import messages
from django.views import View
from django.http import JsonResponse
from quiz.admin.mixins import AdminRequiredMixin
from quiz.models import Quiz, QuizResult, Category # removed User from here cause of error
from users.models import CustomUser  # If you're using a custom user model
from ...models import Quiz, QuizResult, Category, UserAchievement
from django.contrib.auth import get_user_model
from quiz.analytics import QuizAnalytics
from django.db.models import Count, Avg, Sum, F
from django.db.models.functions import TruncDate
from django.utils import timezone
from datetime import datetime, timedelta
from ..mixins import AdminViewMixin
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin

from quiz.models import QuizSettings
from ..forms import QuizSettingsForm


User = get_user_model()

class DashboardView(AdminRequiredMixin, TemplateView):  # Change from LoginRequiredMixin to AdminRequiredMixin
    template_name = 'admin/quiz/dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'total_quizzes': Quiz.objects.count(),
            'total_users': User.objects.count(),
            'total_categories': Category.objects.count(),
            'recent_results': QuizResult.objects.select_related('user', 'quiz')\
                            .order_by('-completed_at')[:5]
        })
        return context

class DashboardStatsView(AdminRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        analytics = QuizAnalytics()
        
        # Get time range from request
        days = int(request.GET.get('days', 30))
        end_date = timezone.now()
        start_date = end_date - timedelta(days=days)
        
        # Get recent activity
        recent_activity = QuizResult.objects.select_related('user', 'quiz')\
            .order_by('-completed_at')[:5]\
            .values(
                'user__username',
                'quiz__title',
                'score',
                'time_taken',
                'completed_at'
            )

        return JsonResponse({
            'overview': {
                'total_users': User.objects.count(),
                'total_quizzes': Quiz.objects.count(),
                'total_attempts': QuizResult.objects.count(),
                'avg_score': round(QuizResult.objects.aggregate(Avg('score'))['score__avg'] or 0, 1)
            },
            'trends': list(analytics.get_trend_data(days=days)),
            'categoryPerformance': [{
                'name': cat.name,
                'avgScore': round(cat.avg_score or 0, 2),
                'totalAttempts': cat.total_attempts
            } for cat in analytics.get_category_performance()],
            'recentActivity': [{
                'user': activity['user__username'],
                'quiz': activity['quiz__title'],
                'score': activity['score'],
                'time_taken': activity['time_taken'],
                'completed_at': activity['completed_at'].isoformat()
            } for activity in recent_activity]
        })


def dashboard_stats(request):
    """API endpoint for dashboard statistics"""
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'Authentication required'}, status=401)

    # Get date range for trend data (last 7 days)
    end_date = timezone.now()
    start_date = end_date - timedelta(days=6)
    
    # Get daily quiz attempts trend
    trends = QuizResult.objects.filter(
        completed_at__gte=start_date,
        completed_at__lte=end_date
    ).annotate(
        date=TruncDate('completed_at')
    ).values('date').annotate(
        attempts=Count('id')
    ).order_by('date')

    # Fill in missing dates with zero attempts
    trend_data = []
    current_date = start_date.date()
    date_attempts = {t['date']: t['attempts'] for t in trends}
    
    while current_date <= end_date.date():
        trend_data.append({
            'date': current_date.strftime('%Y-%m-%d'),
            'attempts': date_attempts.get(current_date, 0)
        })
        current_date += timedelta(days=1)

    # Get category performance data
    category_performance = Category.objects.annotate(
        totalAttempts=Count('quiz__quizresult'),
        avgScore=Avg('quiz__quizresult__score')
    ).values('name', 'totalAttempts', 'avgScore')

    # Get top users
    top_users = User.objects.annotate(
        quizCount=Count('quizresult'),
        avgScore=Avg('quizresult__score')
    ).filter(quizCount__gt=0).order_by('-avgScore')[:5].values(
        'username', 'quizCount', 'avgScore'
    )

    # Get today's overview
    today_start = timezone.now().replace(hour=0, minute=0, second=0, microsecond=0)
    overview = {
        'total_quizzes_taken': QuizResult.objects.filter(
            completed_at__gte=today_start
        ).count()
    }

    return JsonResponse({
        'trends': trend_data,
        'categoryPerformance': list(category_performance),
        'topUsers': list(top_users),
        'overview': overview
    })



class AnalyticsView(AdminRequiredMixin, TemplateView):
    template_name = 'admin/quiz/analytics.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'total_quizzes': Quiz.objects.count(),
            'total_users': User.objects.count(),
            'total_attempts': QuizResult.objects.count(),
            'recent_attempts': QuizResult.objects.select_related('user', 'quiz')\
                             .order_by('-completed_at')[:5]
        })
        return context

class SettingsView(AdminRequiredMixin, FormView):
    template_name = 'admin/quiz/settings.html'
    form_class = QuizSettingsForm
    success_url = reverse_lazy('quiz_admin:settings')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['instance'] = QuizSettings.get_settings()
        return kwargs

    def form_valid(self, form):
        form.save()
        messages.success(self.request, 'Settings updated successfully.')
        return super().form_valid(form)

    def form_invalid(self, form):
        messages.error(self.request, 'Please correct the errors below.')
        return super().form_invalid(form)
