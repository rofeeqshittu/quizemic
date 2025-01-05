# quiz/analytics.py

from django.db.models import Avg, Count, Sum, F, ExpressionWrapper, FloatField, Case, When, Q
from django.db.models.functions import ExtractHour, ExtractDay, TruncDate
from django.utils import timezone
from datetime import timedelta
from .models import Quiz, QuizResult, Category, Achievement, UserAchievement 
import json

class QuizAnalytics:
    @staticmethod
    def get_overview_stats():
        """Get overall quiz statistics."""
        return {
            'total_quizzes_taken': QuizResult.objects.count(),
            'total_active_quizzes': Quiz.objects.filter(is_active=True).count(),
            'avg_score': QuizResult.objects.aggregate(
                avg=Avg('score')
            )['avg'] or 0,
            'total_users': QuizResult.objects.values('user').distinct().count()
        }

    @staticmethod
    def get_category_performance():
        """Get performance statistics by category."""
        return Category.objects.annotate(
            quiz_count=Count('quiz'),
            total_attempts=Count('quiz__quizresult'),
            avg_score=Avg('quiz__quizresult__score'),
            completion_rate=ExpressionWrapper(
                Count('quiz__quizresult', filter=Q(quiz__quizresult__score__gt=0)) * 100.0 /
                Case(
                    When(total_attempts=0, then=1),
                    default=F('total_attempts'),
                    output_field=FloatField()
                ),
                output_field=FloatField()
            )
        )

    @staticmethod
    def get_time_distribution():
        """Get quiz completion time distribution."""
        return QuizResult.objects.annotate(
            hour=ExtractHour('completed_at')
        ).values('hour').annotate(
            count=Count('id'),
            avg_score=Avg('score')
        ).order_by('hour')

    @staticmethod
    def get_trend_data(days=30):
        """Get trend data for the specified number of days."""
        start_date = timezone.now() - timedelta(days=days)
        return QuizResult.objects.filter(
            completed_at__gte=start_date
        ).annotate(
            date=TruncDate('completed_at')
        ).values('date').annotate(
            attempts=Count('id'),
            avg_score=Avg('score')
        ).order_by('date')

    @staticmethod
    def get_user_progress(user):
        """Get detailed progress for a specific user."""
        return {
            'total_quizzes': QuizResult.objects.filter(user=user).count(),
            'avg_score': QuizResult.objects.filter(user=user).aggregate(
                avg=Avg('score')
            )['avg'] or 0,
            'category_breakdown': QuizResult.objects.filter(user=user).values(
                'quiz__category__name'
            ).annotate(
                attempts=Count('id'),
                avg_score=Avg('score')
            ),
            'recent_improvement': QuizResult.objects.filter(
                user=user
            ).order_by('-completed_at')[:10]
        }


class AchievementTracker:
    ACHIEVEMENTS = {
        'perfect_score': {
            'title': 'Perfect Score',
            'description': 'Score 100% on any quiz',
            'icon': '🌟',
            'check_type': 'single_quiz',
            'threshold': 100
        },
        'speed_demon': {
            'title': 'Speed Demon',
            'description': 'Complete a quiz in less than half the allowed time',
            'icon': '⚡',
            'check_type': 'time_based',
            'threshold': 0.5
        },
        'persistent': {
            'title': 'Persistent Learner',
            'description': 'Complete 10 quizzes in a category',
            'icon': '📚',
            'check_type': 'category_count',
            'threshold': 10
        },
        'category_master': {
            'title': 'Category Master',
            'description': 'Achieve 90%+ average in a category',
            'icon': '👑',
            'check_type': 'category_average',
            'threshold': 90
        }
    }

    @classmethod
    def check_achievements(cls, quiz_result):
        """Check and award achievements for a quiz result."""
        achievements = []
        user = quiz_result.user
        
        # Check single quiz achievements
        if cls._check_single_quiz_achievement(quiz_result):
            achievements.append(cls.ACHIEVEMENTS['perfect_score'])
            
        if cls._check_time_based_achievement(quiz_result):
            achievements.append(cls.ACHIEVEMENTS['speed_demon'])

        # Check category-based achievements
        category_stats = cls._get_category_stats(user, quiz_result.quiz.category)
        
        if category_stats['count'] >= cls.ACHIEVEMENTS['persistent']['threshold']:
            achievements.append(cls.ACHIEVEMENTS['persistent'])
        
        if category_stats['avg_score'] >= cls.ACHIEVEMENTS['category_master']['threshold']:
            achievements.append(cls.ACHIEVEMENTS['category_master'])

        # Save achievements to database
        cls._save_achievements(user, achievements, quiz_result)
        
        return achievements

    @classmethod
    def _check_single_quiz_achievement(cls, quiz_result):
        """Check achievements that depend on a single quiz result."""
        return quiz_result.score == cls.ACHIEVEMENTS['perfect_score']['threshold']

    @classmethod
    def _check_time_based_achievement(cls, quiz_result):
        """Check time-based achievements."""
        if not quiz_result.time_taken or not quiz_result.quiz.time_limit:
            return False
        return quiz_result.time_taken < (quiz_result.quiz.time_limit * cls.ACHIEVEMENTS['speed_demon']['threshold'])

    @classmethod
    def _get_category_stats(cls, user, category):
        """Get category statistics for a user."""
        results = QuizResult.objects.filter(
            user=user,
            quiz__category=category
        )
        
        return {
            'count': results.count(),
            'avg_score': results.aggregate(Avg('score'))['score__avg'] or 0
        }

    @classmethod
    def _save_achievements(cls, user, achievements, quiz_result):
        """Save earned achievements to the database."""
        for achievement in achievements:
            UserAchievement.objects.get_or_create(
                user=user,
                achievement_key=next(
                    key for key, value in cls.ACHIEVEMENTS.items() 
                    if value['title'] == achievement['title']
                ),
                defaults={
                    'earned_at': quiz_result.completed_at,
                    'quiz_result': quiz_result,
                    'achievement_data': {
                        'title': achievement['title'],
                        'description': achievement['description'],
                        'icon': achievement['icon']
                    }
                }
            )

    @classmethod
    def get_user_achievements(cls, user):
        """Get all achievements for a user."""
        return UserAchievement.objects.filter(user=user).select_related('quiz_result')
