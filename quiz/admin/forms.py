# quiz/admin/forms.py (create this file if it doesn't exist)

from django import forms
from quiz.models import QuizSettings, Quiz, Question, Answer

class QuizForm(forms.ModelForm):
    class Meta:
        model = Quiz
        fields = ['title', 'category', 'description', 'time_limit', 'is_active']

    def clean(self):
        cleaned_data = super().clean()
        
        # Check if we have any questions in the POST data
        has_questions = False
        for key in self.data.keys():
            if key.startswith('new_question_text[]') and self.data.get(key).strip():
                has_questions = True
                break
                
        if not has_questions:
            raise forms.ValidationError("A quiz must have at least one question.")
            
        return cleaned_data

class QuizSettingsForm(forms.ModelForm):
    class Meta:
        model = QuizSettings
        fields = [
            'default_time_limit',
            'points_per_question',
            'show_correct_answers',
            'notify_new_quiz',
            'notify_results',
            'enable_leaderboard',
            'minimum_pass_score',
            'max_attempts_per_quiz',
        ]
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Add Bootstrap classes to form fields
        for field in self.fields.values():
            field.widget.attrs['class'] = 'form-control'
        
        # For checkbox fields, use a different class
        for field_name in ['show_correct_answers', 'notify_new_quiz', 'notify_results', 'enable_leaderboard']:
            self.fields[field_name].widget.attrs['class'] = 'form-check-input'
