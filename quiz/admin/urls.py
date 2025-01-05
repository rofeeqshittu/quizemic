# quiz/admin/urls.py

from django.urls import path
from .views import dashboard, quiz, user, category, achievement
from .views.category import (
    CategoryListView, CategoryCreateView, CategoryUpdateView, CategoryDeleteView,
    CategoryAPIView, category_create_api
)
from .views.dashboard import DashboardView, dashboard_stats

app_name = 'quiz_admin'

urlpatterns = [
    # Dashboard
    path('', dashboard.DashboardView.as_view(), name='dashboard'),
    path('api/dashboard-stats/', dashboard.DashboardStatsView.as_view(), name='dashboard_stats'),  # Keep only one stats endpoint

    # Quiz Management
    path('quizzes/', quiz.QuizListView.as_view(), name='quiz_list'),
    path('quizzes/create/', quiz.QuizCreateView.as_view(), name='quiz_create'),
    path('quizzes/<int:pk>/', quiz.QuizUpdateView.as_view(), name='quiz_update'),
    path('quizzes/<int:pk>/delete/', quiz.QuizDeleteView.as_view(), name='quiz_delete'),
    path('quizzes/<int:quiz_id>/questions/', quiz.QuestionListView.as_view(), name='question_list'),
    path('quizzes/<int:quiz_id>/questions/create/', quiz.QuestionCreateView.as_view(), name='question_create'),
    path('quizzes/questions/<int:pk>/', quiz.QuestionUpdateView.as_view(), name='question_edit'),
    path('quizzes/questions/<int:pk>/delete/', quiz.QuestionDeleteView.as_view(), name='question_delete'),
    
    # User Management
    path('users/', user.UserListView.as_view(), name='user_list'),
    path('users/<int:pk>/', user.UserDetailView.as_view(), name='user_detail'),
    path('users/<int:pk>/activity/', user.UserActivityView.as_view(), name='user_activity'),
    path('users/create/', user.UserCreateView.as_view(), name='user_create'),
    path('users/<int:pk>/edit/', user.UserUpdateView.as_view(), name='user_edit'),
    path('users/<int:pk>/delete/', user.UserDeleteView.as_view(), name='user_delete'),
    path('users/<int:pk>/toggle-active/', user.UserToggleActiveView.as_view(), name='user_toggle_active'),

    
    # Category Management
    path('categories/', category.CategoryListView.as_view(), name='category_list'),
    path('categories/create/', category.CategoryCreateView.as_view(), name='category_create'),
    path('categories/<int:pk>/', category.CategoryUpdateView.as_view(), name='category_update'),
    path('categories/<int:pk>/delete/', category.CategoryDeleteView.as_view(), name='category_delete'),
    # New Category API endpoints
    path('api/categories/', category_create_api, name='category_create_api'),
    path('api/categories/<int:pk>/', category.CategoryAPIView.as_view(), name='category_api'),

    
    # Achievement Management
    path('achievements/', achievement.AchievementListView.as_view(), name='achievement_list'),
    path('achievements/create/', achievement.AchievementCreateView.as_view(), name='achievement_create'),
    path('achievements/<int:pk>/', achievement.AchievementUpdateView.as_view(), name='achievement_update'),
    path('achievements/<int:pk>/delete/', achievement.AchievementDeleteView.as_view(), name='achievement_delete'),
    
    # Analytics
    path('analytics/', dashboard.AnalyticsView.as_view(), name='analytics'),
    path('settings/', dashboard.SettingsView.as_view(), name='settings'),

]
