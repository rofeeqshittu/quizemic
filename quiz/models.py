# quiz/models.py

from django.db import models
from django.conf import settings
from django.utils import timezone  # for Nigeria timing

class Category(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    icon = models.CharField(max_length=50, blank=True)  # For FontAwesome icons
    
    class Meta:
        verbose_name_plural = "Categories"
    
    def __str__(self):
        return self.name

class Quiz(models.Model):
    title = models.CharField(max_length=200)
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    description = models.TextField()
    time_limit = models.IntegerField(help_text="Time limit in minutes")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name_plural = "Quizzes"

    def __str__(self):
        return self.title

class Question(models.Model):
    quiz = models.ForeignKey(Quiz, related_name='questions', on_delete=models.CASCADE)
    text = models.TextField()
    description = models.TextField(blank=True, help_text="Additional guidance or description for the question")
    points = models.IntegerField(default=1)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.text[:50]

class Answer(models.Model):
    question = models.ForeignKey(Question, related_name='answers', on_delete=models.CASCADE)
    text = models.CharField(max_length=200)
    is_correct = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.text} - {'Correct' if self.is_correct else 'Incorrect'}"


class QuizResult(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE)
    score = models.IntegerField()
    time_taken = models.IntegerField(help_text="Time taken in seconds")
    completed_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ['-completed_at']
        get_latest_by = 'completed_at'  # Add this line


    def __str__(self):
        return f"{self.user.username} - {self.quiz.title} - {self.score}"

class UserAnswer(models.Model):
    quiz_result = models.ForeignKey(QuizResult, related_name='user_answers', on_delete=models.CASCADE)
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    answer = models.ForeignKey(Answer, on_delete=models.CASCADE)

    class Meta:
        unique_together = ['quiz_result', 'question']

    def __str__(self):
        return f"{self.quiz_result.user.username} - {self.question.text[:30]}"

class Achievement(models.Model):
    key = models.CharField(max_length=50, unique=True)
    title = models.CharField(max_length=100)
    description = models.TextField()
    icon = models.CharField(max_length=20)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.title
        
    @property
    def earned_count(self):
        return UserAchievement.objects.filter(achievement_key=self.key).count()


class UserAchievement(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='achievements', on_delete=models.CASCADE)
    achievement_key = models.CharField(max_length=50)
    earned_at = models.DateTimeField(default=timezone.now)
    quiz_result = models.ForeignKey('QuizResult', on_delete=models.CASCADE, null=True, blank=True)
    achievement_data = models.JSONField(default=dict)
    
    class Meta:
        unique_together = ['user', 'achievement_key']
        ordering = ['-earned_at']
    
    def __str__(self):
        return f"{self.user.username} - {self.achievement_data.get('title', self.achievement_key)}"
    
    @property
    def title(self):
        return self.achievement_data.get('title', '')
    
    @property
    def description(self):
        return self.achievement_data.get('description', '')
    
    @property
    def icon(self):
        return self.achievement_data.get('icon', '')


class QuizSettings(models.Model):
    # General Settings
    default_time_limit = models.PositiveIntegerField(
        default=30,
        help_text="Default time limit for quizzes in minutes"
    )
    points_per_question = models.PositiveIntegerField(
        default=1,
        help_text="Default points awarded per correct question"
    )
    show_correct_answers = models.BooleanField(
        default=True,
        help_text="Show correct answers after quiz completion"
    )

    # Email Settings
    notify_new_quiz = models.BooleanField(
        default=False,
        help_text="Send notifications when new quizzes are available"
    )
    notify_results = models.BooleanField(
        default=True,
        help_text="Send quiz results via email"
    )

    # Additional Settings
    enable_leaderboard = models.BooleanField(
        default=True,
        help_text="Enable the leaderboard feature"
    )
    minimum_pass_score = models.PositiveIntegerField(
        default=60,
        help_text="Minimum score required to pass a quiz (percentage)"
    )
    max_attempts_per_quiz = models.PositiveIntegerField(
        default=3,
        help_text="Maximum number of attempts allowed per quiz"
    )

    class Meta:
        verbose_name = "Quiz Settings"
        verbose_name_plural = "Quiz Settings"

    @classmethod
    def get_settings(cls):
        """Get the settings instance, creating it if it doesn't exist"""
        settings, created = cls.objects.get_or_create(pk=1)
        return settings
