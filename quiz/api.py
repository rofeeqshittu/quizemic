# quiz/api.py

from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods
from .analytics import QuizAnalytics, AchievementTracker
from .models import Quiz, QuizResult
from django.utils import timezone

@login_required
@require_http_methods(["GET"])
def get_analytics(request):
    """Get all analytics data."""
    analytics = QuizAnalytics()
    return JsonResponse({
        'overview': analytics.get_overview_stats(),
        'category_performance': list(analytics.get_category_performance()),
        'time_distribution': list(analytics.get_time_distribution()),
        'trends': list(analytics.get_trend_data())
    })

@login_required
@require_http_methods(["GET"])
def get_user_analytics(request):
    """Get user-specific analytics."""
    analytics = QuizAnalytics()
    progress = analytics.get_user_progress(request.user)
    return JsonResponse(progress)

@login_required
@require_http_methods(["GET"])
def get_quiz_analytics(request, quiz_id):
    """Get analytics for a specific quiz."""
    quiz = Quiz.objects.get(id=quiz_id)
    results = QuizResult.objects.filter(quiz=quiz)
    
    analytics = {
        'total_attempts': results.count(),
        'avg_score': results.aggregate(Avg('score'))['score__avg'] or 0,
        'avg_time': results.aggregate(Avg('time_taken'))['time_taken__avg'] or 0,
        'completion_rate': (
            results.filter(score__gt=0).count() / results.count() * 100
            if results.count() > 0 else 0
        ),
        'score_distribution': list(results.values('score').annotate(
            count=Count('id')
        ).order_by('score')),
        'recent_attempts': list(results.order_by('-completed_at')[:10].values(
            'user__username', 'score', 'time_taken', 'completed_at'
        ))
    }
    
    return JsonResponse(analytics)

@login_required
@require_http_methods(["GET"])
def get_achievements(request):
    """Get user achievements."""
    user_results = QuizResult.objects.filter(user=request.user)
    achievements = []
    
    for result in user_results:
        new_achievements = AchievementTracker.check_achievements(result)
        achievements.extend(new_achievements)
    
    # Remove duplicates while preserving order
    unique_achievements = []
    seen = set()
    for achievement in achievements:
        if achievement['title'] not in seen:
            unique_achievements.append(achievement)
            seen.add(achievement['title'])
    
    return JsonResponse({
        'achievements': unique_achievements,
        'total_count': len(unique_achievements)
    })
