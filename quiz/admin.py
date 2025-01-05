# quiz/admin.py

from django.contrib import admin
from django.contrib.admin import AdminSite
from django.urls import path
from django.template.response import TemplateResponse
from django.utils import timezone
from django.db.models import Count, Avg, F
from django.db.models.functions import TruncDate
from datetime import timedelta
from django.utils.html import format_html
from .models import Category, Quiz, Question, Answer, QuizResult



# Keep your existing model registrations
admin.site.register(Category, CategoryAdmin)
admin.site.register(Quiz, QuizAdmin)
admin.site.register(Question, QuestionAdmin)
admin.site.register(QuizResult, QuizResultAdmin)

# Remove or comment out the QuizAdminSite class and admin_site variable
# We'll handle custom admin through our quiz-admin URLs instead


class AnswerInline(admin.TabularInline):
    model = Answer
    extra = 4
    fields = ['text', 'is_correct']

class QuestionInline(admin.StackedInline):
    model = Question
    extra = 1
    fields = ['text', 'description', 'points']
    show_change_link = True

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'quiz_count', 'total_questions']
    search_fields = ['name']

    def quiz_count(self, obj):
        return obj.quiz_set.count()
    quiz_count.short_description = 'Quizzes'

    def total_questions(self, obj):
        return Question.objects.filter(quiz__category=obj).count()
    total_questions.short_description = 'Total Questions'

@admin.register(Quiz)
class QuizAdmin(admin.ModelAdmin):
    list_display = ['title', 'category', 'question_count', 'avg_score', 'completion_rate', 'is_active']
    list_filter = ['category', 'is_active', 'created_at']
    search_fields = ['title', 'description']
    inlines = [QuestionInline]
    actions = ['activate_quizzes', 'deactivate_quizzes']

    def question_count(self, obj):
        return obj.questions.count()
    question_count.short_description = 'Questions'

    def avg_score(self, obj):
        results = obj.quizresult_set.all()
        if not results:
            return '0%'
        avg = sum(r.score for r in results) / len(results)
        return f'{avg:.1f}%'
    avg_score.short_description = 'Avg Score'

    def completion_rate(self, obj):
        total = obj.quizresult_set.count()
        if not total:
            return '0%'
        completed = obj.quizresult_set.filter(score__gt=0).count()
        rate = (completed / total) * 100
        return f'{rate:.1f}%'
    completion_rate.short_description = 'Completion Rate'

    def activate_quizzes(self, request, queryset):
        queryset.update(is_active=True)
    activate_quizzes.short_description = 'Activate selected quizzes'

    def deactivate_quizzes(self, request, queryset):
        queryset.update(is_active=False)
    deactivate_quizzes.short_description = 'Deactivate selected quizzes'

@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ['truncated_text', 'quiz', 'points', 'answer_count']
    list_filter = ['quiz__category', 'quiz']
    search_fields = ['text', 'quiz__title']
    inlines = [AnswerInline]

    def truncated_text(self, obj):
        return obj.text[:100] + '...' if len(obj.text) > 100 else obj.text
    truncated_text.short_description = 'Question'

    def answer_count(self, obj):
        return obj.answers.count()
    answer_count.short_description = 'Answers'

@admin.register(QuizResult)
class QuizResultAdmin(admin.ModelAdmin):
    list_display = ['user', 'quiz', 'score', 'formatted_time_taken', 'completed_at']
    list_filter = ['quiz__category', 'completed_at', 'quiz']
    search_fields = ['user__username', 'quiz__title']
    readonly_fields = ['completed_at']

    def formatted_time_taken(self, obj):
        minutes = obj.time_taken // 60
        seconds = obj.time_taken % 60
        return f'{minutes}m {seconds}s'
    formatted_time_taken.short_description = 'Time Taken'


#   ADMIN SECTION
class QuizAdminSite(AdminSite):
    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('analytics/', self.admin_view(self.analytics_view), name='quiz-analytics'),
        ]
        return custom_urls + urls

    def analytics_view(self, request):
        # Get date range
        days = int(request.GET.get('days', 30))
        start_date = timezone.now() - timedelta(days=days)

        # General stats
        context = {
            'title': 'Quiz System Analytics',
            'total_users': QuizResult.objects.values('user').distinct().count(),
            'total_quizzes_taken': QuizResult.objects.count(),
            'active_quizzes': Quiz.objects.filter(is_active=True).count(),
            'total_categories': Category.objects.count(),

            # Time-based metrics
            'daily_results': QuizResult.objects.filter(
                completed_at__gte=start_date
            ).annotate(
                date=TruncDate('completed_at')
            ).values('date').annotate(
                count=Count('id'),
                avg_score=Avg('score')
            ).order_by('date'),

            # Category metrics
            'category_stats': Category.objects.annotate(
                quiz_count=Count('quiz'),
                total_attempts=Count('quiz__quizresult'),
                avg_score=Avg('quiz__quizresult__score')
            ),

            # User engagement
            'top_performers': QuizResult.objects.values(
                'user__username'
            ).annotate(
                total_quizzes=Count('id'),
                avg_score=Avg('score')
            ).order_by('-avg_score')[:10],

            # Quiz performance
            'quiz_stats': Quiz.objects.annotate(
                attempt_count=Count('quizresult'),
                avg_score=Avg('quizresult__score'),
                avg_time=Avg('quizresult__time_taken')
            ).order_by('-attempt_count')[:10],

            # Recent activity
            'recent_results': QuizResult.objects.select_related(
                'user', 'quiz'
            ).order_by('-completed_at')[:20],

            # Usage patterns
            'completion_rates': Quiz.objects.annotate(
                    total_attempts=Count('quizresult'),
                    completed=Count('quizresult', filter=F('quizresult__score__gt=0'))
             ).annotate(
                    completion_rate=F('completed') * 100.0 / F('total_attempts')
             ),
         }

        return TemplateResponse(request, 'admin/quiz/analytics.html', context)

# Replace the default admin site
admin_site = QuizAdminSite(name='quiz_admin')
