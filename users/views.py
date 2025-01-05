# users/views.py

from django.shortcuts import render, redirect
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.db.models import Sum, Avg, Count
from datetime import datetime, timedelta
from .forms import CustomUserCreationForm, CustomAuthenticationForm
from quiz.models import QuizResult, Quiz

def register(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, 'Account created successfully!')
            return redirect('quiz_home')
    else:
        form = CustomUserCreationForm()
    return render(request, 'users/register.html', {'form': form})

@login_required
def profile(request):
    # Get user's quiz results
    user_results = QuizResult.objects.filter(user=request.user).order_by('-completed_at')
    recent_quizzes = user_results[:5]

    # Calculate statistics
    total_quizzes = user_results.count()
    avg_score = user_results.aggregate(Avg('score'))['score__avg'] or 0
    total_time = user_results.aggregate(total_time=Sum('time_taken'))['total_time'] or 0

    # Calculate achievements
    achievements = []

    # Perfect Score Achievement
    perfect_scores = user_results.filter(score=100).count()
    if perfect_scores > 0:
        achievements.append({
            'title': 'Perfect Score',
            'icon': '🌟',
            'description': f'Achieved 100% in {perfect_scores} quiz{"es" if perfect_scores > 1 else ""}',
            'date': user_results.filter(score=100).first().completed_at.strftime('%Y-%m-%d')
        })

    # Quick Learner Achievement
    week_ago = datetime.now() - timedelta(days=7)
    weekly_quizzes = user_results.filter(completed_at__gte=week_ago).count()
    if weekly_quizzes >= 10:
        achievements.append({
            'title': 'Quick Learner',
            'icon': '📚',
            'description': 'Completed 10 quizzes in a week',
            'date': datetime.now().strftime('%Y-%m-%d')
        })

    # Category Mastery
    category_stats = user_results.values('quiz__category__name').annotate(
        avg_score=Avg('score'),
        quiz_count=Count('id')
    ).filter(quiz_count__gte=5, avg_score__gte=90)

    for stat in category_stats:
        achievements.append({
            'title': f'{stat["quiz__category__name"]} Master',
            'icon': '🏅',
            'description': f'Averaged {stat["avg_score"]:.1f}% in {stat["quiz_count"]} quizzes',
            'date': datetime.now().strftime('%Y-%m-%d')
        })

    # Get performance data for charts
    performance_data = {
        '1M': get_performance_data(user_results, 30),
        '3M': get_performance_data(user_results, 90),
        '6M': get_performance_data(user_results, 180),
    }

    # Get category breakdown
    category_breakdown = user_results.values('quiz__category__name').annotate(
        total_quizzes=Count('id'),
        avg_score=Avg('score')
    ).order_by('-total_quizzes')

    context = {
        'user': request.user,
        'total_quizzes': total_quizzes,
        'avg_score': round(avg_score, 1),
        'total_time': total_time,
        'achievements': achievements,
        'recent_quizzes': recent_quizzes,
        'performance_data': performance_data,
        'category_breakdown': category_breakdown,
    }

    return render(request, 'users/profile.html', context)

def get_performance_data(results, days):
    start_date = datetime.now() - timedelta(days=days)
    period_results = results.filter(completed_at__gte=start_date)

    if days <= 30:  # Group by week for 1M
        data = []
        for week in range(4):
            week_start = start_date + timedelta(days=week*7)
            week_end = week_start + timedelta(days=7)
            week_results = period_results.filter(
                completed_at__range=[week_start, week_end]
            )
            avg_score = week_results.aggregate(Avg('score'))['score__avg'] or 0
            data.append({
                'date': f'Week {week+1}',
                'score': round(avg_score, 1)
            })
    else:  # Group by month for 3M and 6M
        data = []
        months = days // 30
        for month in range(months):
            month_start = start_date + timedelta(days=month*30)
            month_end = month_start + timedelta(days=30)
            month_results = period_results.filter(
                completed_at__range=[month_start, month_end]
            )
            avg_score = month_results.aggregate(Avg('score'))['score__avg'] or 0
            data.append({
                'date': month_start.strftime('%b'),
                'score': round(avg_score, 1)
            })
    return data

@login_required
def update_profile(request):
    if request.method == 'POST':
        user = request.user
        name_parts = request.POST.get('name', '').split()
        if name_parts:
            user.first_name = name_parts[0]
            user.last_name = ' '.join(name_parts[1:]) if len(name_parts) > 1 else ''

        user.email = request.POST.get('email', '')
        user.bio = request.POST.get('bio', '')

        if 'profile_picture' in request.FILES:
            user.profile_picture = request.FILES['profile_picture']

        user.save()
        messages.success(request, 'Profile updated successfully!')
        return JsonResponse({'status': 'success'})
    return JsonResponse({'status': 'error'}, status=400)
