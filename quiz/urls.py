# quiz/urls.py

from django.urls import path
from .admin import admin_site  # Import the custom admin site
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('quiz/', views.quiz_home, name='quiz_home'),

    path('quizzes/', views.quiz_list, name='quiz_list'),
    path('quiz/<int:quiz_id>/', views.take_quiz, name='take_quiz'),
    path('quiz/<int:quiz_id>/start/', views.start_quiz, name='start_quiz'),
    path('quiz/<int:quiz_id>/question/', views.quiz_question, name='quiz_question'),

    path('quiz/<int:quiz_id>/time-check/', views.quiz_time_check, name='quiz_time_check'),
    path('quiz/<int:quiz_id>/submit/', views.submit_quiz, name='submit_quiz'),
    path('quiz/result/<int:result_id>/', views.quiz_result, name='quiz_result'),

    path('leaderboard/', views.leaderboard, name='leaderboard'),
    path('api/leaderboard/', views.leaderboard_api, name='leaderboard_api'),

    path('api/placeholder/<int:width>/<int:height>/', views.placeholder_image, name='placeholder_image'),

    # Original analytics endpoints
    path('analytics/', views.analytics_view, name='analytics'),
    path('api/analytics/', views.get_analytics, name='get_analytics'),
    path('api/achievements/', views.get_achievements, name='get_achievements'),
    path('api/dashboard-data/', views.dashboard_data, name='dashboard-data'),

    # Additional URL patterns to match the frontend requests
    path('quiz/analytics/data/', views.get_analytics, name='get_analytics'),
    path('quiz/analytics/achievements/', views.get_achievements, name='analytics_achievements'),

    # quiz/urls.py
    path('achievements/', views.achievement_list, name='achievement_list'),
    path('achievements/check/<int:result_id>/', views.check_achievements, name='check_achievements'),
    path('achievements/stats/', views.achievement_stats, name='achievement_stats'),
]
