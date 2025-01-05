# quiz/views.py

from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.http import JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required, permission_required
from django.utils import timezone
from datetime import timedelta
from django.db.models import Count, Sum, Avg, Prefetch
from django.contrib import messages
from .models import Quiz, Category, Question, Answer, QuizResult, UserAnswer, UserAchievement
from django.template.loader import render_to_string
import json
from .analytics import QuizAnalytics, AchievementTracker
from django.contrib.auth.decorators import login_required

User = get_user_model()


def home(request):
    return render(request, 'quiz/home.html')

@login_required
def quiz_home(request):
    categories = Category.objects.all()
    recent_results = QuizResult.objects.filter(user=request.user)[:5]
    context = {
        'categories': categories,
        'recent_results': recent_results
    }
    return render(request, 'quiz/quiz_home.html', context)

# quiz/views.py
def quiz_list(request):
    categories = Category.objects.all()
    selected_category = request.GET.get('category')

    quizzes = Quiz.objects.filter(is_active=True)
    if selected_category:
        quizzes = quizzes.filter(category_id=selected_category)

    context = {
        'categories': categories,
        'quizzes': quizzes,
        'selected_category': selected_category
    }
    return render(request, 'quiz/quiz_list.html', context)


@login_required
def take_quiz(request, quiz_id):
    quiz = get_object_or_404(Quiz, id=quiz_id)
    context = {'quiz': quiz}
    return render(request, 'quiz/take_quiz.html', context)

@login_required
def quiz_result(request, result_id):
    result = get_object_or_404(QuizResult, id=result_id, user=request.user)
    
    # Initialize dictionaries for storing processed data
    questions_data = {}
    user_answers_dict = {}
    correct_questions = []
    
    # Get all user answers for this quiz result
    user_answers = result.user_answers.select_related('question', 'answer').all()
    
    for question in result.quiz.questions.all():
        # Initialize the nested dictionary for this question
        questions_data[str(question.id)] = {
            'user_answer': None,
            'correct_answer': None
        }
        
        # Get user's answer for this question
        user_answer = user_answers.filter(question=question).first()
        if user_answer:
            questions_data[str(question.id)]['user_answer'] = user_answer.answer.text
            user_answers_dict[str(question.id)] = user_answer.answer.text
            if user_answer.answer.is_correct:
                correct_questions.append(question.id)
        
        # Get correct answer
        correct_answer = question.answers.filter(is_correct=True).first()
        if correct_answer:
            questions_data[str(question.id)]['correct_answer'] = correct_answer.text
    
    context = {
        'result': result,
        'correct_questions': correct_questions,
        'questions_data': questions_data,
        'user_answers': user_answers_dict
    }
    return render(request, 'quiz/quiz_result.html', context)


@login_required
def start_quiz(request, quiz_id):
    quiz = get_object_or_404(Quiz, id=quiz_id, is_active=True)

    # Initialize quiz session data
    request.session[f'quiz_{quiz_id}_start_time'] = timezone.now().timestamp()
    request.session[f'quiz_{quiz_id}_current_question'] = 1
    request.session[f'quiz_{quiz_id}_answers'] = {}

    return redirect('quiz_question', quiz_id=quiz_id)

@login_required
def quiz_question(request, quiz_id):
    quiz = get_object_or_404(Quiz, id=quiz_id, is_active=True)
    questions = quiz.questions.all()
    total_questions = questions.count()

    # Get current question number from session
    current_question_number = request.session.get(f'quiz_{quiz_id}_current_question', 1)

    # Check if quiz time has expired
    start_time = request.session.get(f'quiz_{quiz_id}_start_time')
    if start_time:
        elapsed_time = int(timezone.now().timestamp() - start_time)
        time_remaining = (quiz.time_limit * 60) - elapsed_time

        if time_remaining <= 0:
            return submit_quiz(request, quiz_id)
    else:
        time_remaining = quiz.time_limit * 60

    # Get current question
    try:
        current_question = questions[current_question_number - 1]
    except IndexError:
        return submit_quiz(request, quiz_id)

    # Calculate progress
    progress_percentage = (current_question_number / total_questions) * 100

    # Handle answer submission
    if request.method == 'POST':
        answer_id = request.POST.get('answer')
        if answer_id:
            # Store answer in session
            request.session[f'quiz_{quiz_id}_answers'][str(current_question.id)] = answer_id
            request.session.modified = True

            # Move to next question
            if current_question_number < total_questions:
                request.session[f'quiz_{quiz_id}_current_question'] = current_question_number + 1
                return redirect('quiz_question', quiz_id=quiz_id)
            else:
                return submit_quiz(request, quiz_id)

    context = {
        'quiz': quiz,
        'question': current_question,
        'answers': current_question.answers.all(),
        'current_question_number': current_question_number,
        'total_questions': total_questions,
        'is_first_question': current_question_number == 1,
        'is_last_question': current_question_number == total_questions,
        'progress_percentage': progress_percentage,
        'time_remaining': time_remaining,
    }

    return render(request, 'quiz/quiz_page.html', context)


@login_required
def quiz_time_check(request, quiz_id):
    quiz = get_object_or_404(Quiz, id=quiz_id)
    start_time = request.session.get(f'quiz_{quiz_id}_start_time')
    if start_time:
        elapsed_time = int(timezone.now().timestamp() - start_time)
        time_remaining = (quiz.time_limit * 60) - elapsed_time
        return JsonResponse({'timeRemaining': max(0, time_remaining)})
    return JsonResponse({'timeRemaining': quiz.time_limit * 60})

@login_required
def submit_quiz(request, quiz_id):
    quiz = get_object_or_404(Quiz, id=quiz_id)

    # Calculate score
    user_answers = request.session.get(f'quiz_{quiz_id}_answers', {})
    score = 0
    total_points = 0

    # Create the quiz result first
    result = QuizResult.objects.create(
        user=request.user,
        quiz=quiz,
        score=0,  # We'll update this after calculating
        time_taken=int(timezone.now().timestamp() - request.session.get(f'quiz_{quiz_id}_start_time'))
    )

    # Calculate score and save answers
    for question in quiz.questions.all():
        total_points += question.points
        user_answer_id = user_answers.get(str(question.id))
        
        if user_answer_id:
            answer = Answer.objects.get(id=user_answer_id)
            
            # Save the user's answer
            UserAnswer.objects.create(
                quiz_result=result,
                question=question,
                answer=answer
            )
            
            if answer.is_correct:
                score += question.points

    # Calculate and update percentage score
    percentage_score = (score / total_points * 100) if total_points > 0 else 0
    result.score = percentage_score
    result.save()

    # Check for achievements
    new_achievements = AchievementTracker.check_achievements(result)

    # Clear session data
    keys_to_delete = [
        f'quiz_{quiz_id}_start_time',
        f'quiz_{quiz_id}_current_question',
        f'quiz_{quiz_id}_answers'
    ]
    for key in keys_to_delete:
        request.session.pop(key, None)

    messages.success(request, f'Quiz completed! Your score: {percentage_score:.1f}%')

    # If new achievements were earned, add a message
    if new_achievements:
        achievement_names = [a['title'] for a in new_achievements]
        messages.info(request, f'New achievements earned: {", ".join(achievement_names)}!')

    return redirect('quiz_result', result_id=result.id)


# LEADERBOARD VIEWS
# quiz/views.py

@login_required
def leaderboard(request):
    # Get filter parameters
    timeframe = request.GET.get('timeframe', 'all-time')
    category_id = request.GET.get('category', 'all')
    sort_by = request.GET.get('sort', 'score')
    search_query = request.GET.get('search', '')

    # Base queryset for users with their stats
    users_query = User.objects.annotate(
        total_quizzes=Count('quizresult'),
        avg_score=Avg('quizresult__score'),
        earned_points=Sum('quizresult__score')
    ).filter(total_quizzes__gt=0)

    # Time-based filtering
    if timeframe != 'all-time':
        time_threshold = timezone.now()
        if timeframe == 'week':
            time_threshold -= timedelta(days=7)
        elif timeframe == 'month':
            time_threshold -= timedelta(days=30)
        elif timeframe == 'year':
            time_threshold -= timedelta(days=365)
        users_query = users_query.filter(quizresult__completed_at__gte=time_threshold)

    # Category filtering
    if category_id != 'all':
        users_query = users_query.filter(quizresult__quiz__category_id=category_id)

    # Search filtering
    if search_query:
        users_query = users_query.filter(username__icontains=search_query)

    # Sorting
    if sort_by == 'score':
        users_query = users_query.order_by('-earned_points')
    elif sort_by == 'accuracy':
        users_query = users_query.order_by('-avg_score')
    elif sort_by == 'games':
        users_query = users_query.order_by('-total_quizzes')

    # Category leaderboards
    categories = Category.objects.annotate(
        quiz_count=Count('quiz')
    ).filter(quiz_count__gt=0)

    category_leaders = {}
    for category in categories:
        category_leaders[category] = QuizResult.objects.filter(
            quiz__category=category
        ).select_related('user').order_by('-score')[:5]

    context = {
        'top_users': users_query[:10],
        'recent_high_scores': QuizResult.objects.select_related('user', 'quiz')
            .order_by('-score', '-completed_at')[:20],
        'category_leaders': category_leaders,
        'categories': categories,
        'selected_timeframe': timeframe,
        'selected_category': category_id,
        'selected_sort': sort_by,
        'search_query': search_query
    }

    return render(request, 'quiz/leaderboard.html', context)


@login_required
def leaderboard_api(request):
    # Get filter parameters
    timeframe = request.GET.get('timeframe', 'all-time')
    category_id = request.GET.get('category', 'all')
    sort_by = request.GET.get('sort', 'score')
    search_query = request.GET.get('search', '')

    # Base queryset for users with their stats
    users_query = User.objects.annotate(
        total_quizzes=Count('quizresult'),
        avg_score=Avg('quizresult__score'),
        earned_points=Sum('quizresult__score')
    ).filter(total_quizzes__gt=0)

    # Time-based filtering
    if timeframe != 'all-time':
        time_threshold = timezone.now()
        if timeframe == 'week':
            time_threshold -= timedelta(days=7)
        elif timeframe == 'month':
            time_threshold -= timedelta(days=30)
        elif timeframe == 'year':
            time_threshold -= timedelta(days=365)
        users_query = users_query.filter(quizresult__completed_at__gte=time_threshold)

    # Category filtering
    if category_id != 'all':
        users_query = users_query.filter(quizresult__quiz__category_id=category_id)

    # Search filtering
    if search_query:
        users_query = users_query.filter(username__icontains=search_query)

    # Sorting
    if sort_by == 'score':
        users_query = users_query.order_by('-earned_points')
    elif sort_by == 'accuracy':
        users_query = users_query.order_by('-avg_score')
    elif sort_by == 'games':
        users_query = users_query.order_by('-total_quizzes')

    # Get category leaderboards
    categories = Category.objects.annotate(
        quiz_count=Count('quiz')
    ).filter(quiz_count__gt=0)

    category_leaders = {}
    for category in categories:
        category_leaders[category] = QuizResult.objects.filter(
            quiz__category=category
        ).select_related('user').order_by('-score')[:5]

    # Prepare context for template rendering
    context = {
        'top_users': users_query[:10],
        'recent_high_scores': QuizResult.objects.select_related('user', 'quiz')
            .order_by('-score', '-completed_at')[:20],
        'category_leaders': category_leaders,
        'categories': categories,
        'selected_timeframe': timeframe,
        'selected_category': category_id,
        'selected_sort': sort_by,
        'search_query': search_query
    }

    # Render just the leaderboard content
    html = render_to_string('quiz/partials/leaderboard_content.html', context, request)

    return JsonResponse({
        'html': html,
        'success': True
    })


def placeholder_image(request, width: int, height: int):
    """
    Return a JSON response simulating a placeholder for the given dimensions.
    """
    # Example logic: You can generate a dynamic image or just return a JSON response.
    return JsonResponse({'message': f'Placeholder for {width}x{height}'})


# For user/admin Analytics

@login_required
def analytics_view(request):
    """Render the analytics dashboard page."""
    context = {
        'title': 'Quiz Analytics Dashboard',
        'current_page': 'analytics'  # This can help with navigation highlighting
    }
    return render(request, 'quiz/analytics.html', context)

@login_required
def get_analytics(request):
    """API endpoint to get analytics data."""
    analytics = QuizAnalytics()
    data = {
        'overview': analytics.get_overview_stats(),
        'trends': list(analytics.get_trend_data()),
        'category_performance': [
            {
                'name': cat.name,
                'avg_score': cat.avg_score or 0,
                'completion_rate': cat.completion_rate or 0,
                'total_attempts': cat.total_attempts
            }
            for cat in analytics.get_category_performance()
        ],
        'time_distribution': list(analytics.get_time_distribution())
    }
    return JsonResponse(data)

@login_required
def get_achievements(request):
    """API endpoint to get user achievements."""
    # Get user's quiz results
    results = QuizResult.objects.filter(user=request.user)

    # Collect all achievements
    all_achievements = []
    seen_achievements = set()

    for result in results:
        achievements = AchievementTracker.check_achievements(result)
        for achievement in achievements:
            if achievement['title'] not in seen_achievements:
                all_achievements.append(achievement)
                seen_achievements.add(achievement['title'])

    return JsonResponse({
        'achievements': all_achievements
    })


# ANALYTICS API VIEWS

@api_view(['GET'])
@permission_required('quiz.view_quiz')
def dashboard_data(request):
    """Get all dashboard data in a single API call"""
    analytics = QuizAnalytics()

    # Get basic stats
    overview_stats = analytics.get_overview_stats()

    # Get trend data
    trend_data = analytics.get_trend_data(days=30)

    # Get category performance
    category_stats = analytics.get_category_performance()

    # Get recent results
    recent_results = QuizResult.objects.select_related('user', 'quiz').order_by('-completed_at')[:10]

    # Get top performers
    top_performers = QuizResult.objects.values('user__username').annotate(
        quiz_count=Count('id'),
        avg_score=Avg('score')
    ).order_by('-avg_score')[:10]

    return Response({
        'stats': overview_stats,
        'trends': list(trend_data),
        'categoryStats': list(category_stats),
        'recentResults': [{
            'user': result.user.username,
            'quiz': result.quiz.title,
            'score': result.score,
            'time': result.time_taken,
            'completed_at': result.completed_at
        } for result in recent_results],
        'topPerformers': list(top_performers)
    })



# Add these new views here
@login_required
def achievement_list(request):
    """
    Get all achievements for the current user, including both earned and unearned.
    """
    # Get user's earned achievements
    user_achievements = UserAchievement.objects.filter(
        user=request.user
    ).select_related('quiz_result')

    earned_keys = {ua.achievement_key for ua in user_achievements}

    # Prepare all achievements data
    all_achievements = []

    # Add earned achievements
    for user_achievement in user_achievements:
        achievement_data = {
            'key': user_achievement.achievement_key,
            'title': user_achievement.title,
            'description': user_achievement.description,
            'icon': user_achievement.icon,
            'earned': True,
            'earned_at': user_achievement.earned_at.isoformat(),
            'quiz_result': {
                'quiz_title': user_achievement.quiz_result.quiz.title,
                'score': user_achievement.quiz_result.score
            } if user_achievement.quiz_result else None
        }
        all_achievements.append(achievement_data)

    # Add unearned achievements
    for key, achievement in AchievementTracker.ACHIEVEMENTS.items():
        if key not in earned_keys:
            achievement_data = {
                'key': key,
                'title': achievement['title'],
                'description': achievement['description'],
                'icon': achievement['icon'],
                'earned': False,
                'earned_at': None,
                'quiz_result': None
            }
            all_achievements.append(achievement_data)

    return JsonResponse({
        'achievements': all_achievements
    })

@login_required
def check_achievements(request, result_id):
    """
    Manually trigger achievement checking for a specific quiz result.
    """
    quiz_result = get_object_or_404(QuizResult, id=result_id, user=request.user)
    new_achievements = AchievementTracker.check_achievements(quiz_result)

    return JsonResponse({
        'new_achievements': new_achievements
    })

@login_required
def achievement_stats(request):
    """
    Get achievement statistics for the current user.
    """
    total_achievements = len(AchievementTracker.ACHIEVEMENTS)
    earned_achievements = UserAchievement.objects.filter(user=request.user).count()

    stats = {
        'total': total_achievements,
        'earned': earned_achievements,
        'progress': round((earned_achievements / total_achievements) * 100, 1) if total_achievements > 0 else 0
    }

    return JsonResponse(stats)
