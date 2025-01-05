# quiz/admin/views/quiz.py
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.core.exceptions import ValidationError
from django.http import JsonResponse
from django.views.generic import CreateView
from django.db import transaction
from django.http import JsonResponse
from django.urls import reverse_lazy
from django.contrib import messages
from django.db import transaction
from django.shortcuts import redirect
from django.db.models import Count, Avg
from ...models import Quiz, Question, Answer, Category
from django.db import models
from quiz.models import Category, Quiz
from ..mixins import AdminViewMixin, AdminRequiredMixin
from django.shortcuts import get_object_or_404
from ...admin.forms import QuizForm  # add this import


class QuizListView(AdminRequiredMixin, ListView):
    model = Quiz
    template_name = 'admin/quiz/quiz_list.html'
    context_object_name = 'quizzes'
    paginate_by = 9  # Changed to 9 for better grid layout (3x3)

    def get_queryset(self):
        queryset = Quiz.objects.select_related('category').annotate(
            question_count=Count('questions'),
            attempt_count=Count('quizresult'),
            avg_score=Avg('quizresult__score')
        )
        
        # Apply search filter
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(title__icontains=search)
            
        # Apply category filter
        category = self.request.GET.get('category')
        if category:
            queryset = queryset.filter(category_id=category)
            
        return queryset.order_by('-created_at')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['categories'] = Category.objects.all()
        return context

class QuizFormMixin:
    def handle_questions(self, quiz):
        if self.request.POST:
            print("Processing form data:", self.request.POST)

            # Handle existing questions updates
            existing_questions = {q.id: q for q in quiz.questions.all()}
            updated_questions = set()

            # Handle new questions
            new_question_texts = self.request.POST.getlist('new_question_text[]')
            new_question_descriptions = self.request.POST.getlist('new_question_description[]')
            new_question_points = self.request.POST.getlist('new_question_points[]')

            for i, text in enumerate(new_question_texts):
                if text.strip():  # Only create question if text is not empty
                    # Create new question
                    question = Question.objects.create(
                        quiz=quiz,
                        text=text,
                        description=new_question_descriptions[i] if i < len(new_question_descriptions) else '',
                        points=int(new_question_points[i]) if i < len(new_question_points) and new_question_points[i].isdigit() else 1
                )

                # Create answers for this question
                correct_answer = self.request.POST.get(f'new_correct_answer_{i+1}')
                answer_texts = []
                for j in range(4):
                    answer_key = f'new_answer_text[]'
                    answers = self.request.POST.getlist(answer_key)
                    start_idx = i * 4
                    if start_idx + j < len(answers):
                        answer_texts.append(answers[start_idx + j])

                for j, answer_text in enumerate(answer_texts):
                    if answer_text.strip():
                        Answer.objects.create(
                            question=question,
                            text=answer_text,
                            is_correct=(str(j) == str(correct_answer))
                        )


    def handle_answers(self, question, question_id):
        # Get existing answers
        existing_answers = {a.id: a for a in question.answers.all()}
        updated_answers = set()
        
        # Get the correct answer for this question
        correct_answer = self.request.POST.get(f'correct_answer_{question_id}')
        
        # Update existing answers
        for key, value in self.request.POST.items():
            if key.startswith(f'answer_text_{question_id}_'):
                answer_id = int(key.split('_')[-1])
                if answer_id in existing_answers:
                    answer = existing_answers[answer_id]
                    answer.text = value
                    answer.is_correct = str(answer_id) == correct_answer
                    answer.save()
                    updated_answers.add(answer_id)
        
        # Delete answers that weren't updated
        for a_id in existing_answers:
            if a_id not in updated_answers:
                existing_answers[a_id].delete()

    def handle_new_answers(self, question, question_number):
        correct_answer = self.request.POST.get(f'new_correct_answer_{question_number}')
        
        # Create 4 answers for the question
        for i in range(4):
            answer_text = self.request.POST.get(f'new_answer_text_{question_number}_{i}')
            if answer_text:
                Answer.objects.create(
                    question=question,
                    text=answer_text,
                    is_correct=(str(i) == correct_answer)
                )


class QuizCreateView(AdminViewMixin, QuizFormMixin, CreateView):
    model = Quiz
    form_class = QuizForm  # Change this line
    template_name = 'admin/quiz/quiz_form.html'
    success_url = reverse_lazy('quiz_admin:quiz_list')

    def form_invalid(self, form):
        """Return JSON response with form errors"""
        return JsonResponse({
            'success': False,
            'errors': [str(error) for error in form.errors.values()]
        })

    @transaction.atomic
    def form_valid(self, form):
        try:
            # Save the form first
            self.object = form.save()
            
            # Handle questions
            try:
                self.handle_questions(self.object)
            except Exception as e:
                # If question handling fails, roll back and return error
                raise ValidationError(f"Error processing questions: {str(e)}")

            return JsonResponse({
                'success': True,
                'redirect_url': self.get_success_url()
            })
        except ValidationError as e:
            return JsonResponse({
                'success': False,
                'errors': [str(e)]
            })
        except Exception as e:
            return JsonResponse({
                'success': False,
                'errors': [f"An unexpected error occurred: {str(e)}"]
            })

    def handle_questions(self, quiz):
        # Add some debug logging here
        print("Request POST data:", self.request.POST)
        print("Request FILES:", self.request.FILES)
        # Rest of your handle_questions implementation...


class QuizUpdateView(AdminViewMixin, QuizFormMixin, UpdateView):
    model = Quiz
    form_class = QuizForm
    template_name = 'admin/quiz/quiz_form.html'
    success_url = reverse_lazy('quiz_admin:quiz_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['questions'] = self.object.questions.prefetch_related('answers').all()
        return context

    @transaction.atomic
    def form_valid(self, form):
        try:
            # Save the quiz
            self.object = form.save()
            
            # Process existing questions
            existing_question_ids = set()
            for key, value in self.request.POST.items():
                if key.startswith('question_text_') and value.strip():
                    question_id = key.split('_')[-1]
                    try:
                        question = Question.objects.get(id=question_id, quiz=self.object)
                        question.text = value
                        question.description = self.request.POST.get(f'question_description_{question_id}', '')
                        question.points = int(self.request.POST.get(f'question_points_{question_id}', 1))
                        question.save()
                        existing_question_ids.add(int(question_id))
                        
                        # Handle answers for this question
                        self.handle_answers(question, question_id)
                    except Question.DoesNotExist:
                        continue

            # Delete questions that weren't included in the update
            Question.objects.filter(quiz=self.object).exclude(id__in=existing_question_ids).delete()

            # Handle new questions
            self.handle_questions(self.object)

            return JsonResponse({
                'success': True,
                'redirect_url': self.get_success_url()
            })

        except Exception as e:
            transaction.set_rollback(True)
            return JsonResponse({
                'success': False,
                'errors': [str(e)]
            })

    def form_invalid(self, form):
        return JsonResponse({
            'success': False,
            'errors': [str(error) for error in form.errors.values()]
        })

    def handle_answers(self, question, question_id):
        # Get the correct answer for this question
        correct_answer = self.request.POST.get(f'correct_answer_{question_id}')
        
        # Get all answer texts for this question
        answer_texts = []
        for key, value in self.request.POST.items():
            if key.startswith(f'answer_text_{question_id}_') and value.strip():
                answer_id = key.split('_')[-1]
                answer_texts.append((answer_id, value))

        # Update or create answers
        existing_answers = {str(a.id): a for a in question.answers.all()}
        updated_answer_ids = set()

        for answer_id, text in answer_texts:
            if answer_id in existing_answers:
                # Update existing answer
                answer = existing_answers[answer_id]
                answer.text = text
                answer.is_correct = (answer_id == correct_answer)
                answer.save()
                updated_answer_ids.add(answer_id)
            else:
                # Create new answer
                Answer.objects.create(
                    question=question,
                    text=text,
                    is_correct=(answer_id == correct_answer)
                )

        # Delete answers that weren't updated
        for answer_id in existing_answers:
            if answer_id not in updated_answer_ids:
                existing_answers[answer_id].delete()


class QuizDeleteView(AdminViewMixin, DeleteView):
    model = Quiz
    template_name = 'admin/quiz/quiz_confirm_delete.html'
    success_url = reverse_lazy('quiz_admin:quiz_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Add quiz statistics to context
        if self.object.quizresult_set.exists():
            context['total_attempts'] = self.object.quizresult_set.count()
            context['avg_score'] = self.object.quizresult_set.aggregate(
                avg_score=Avg('score')
            )['avg_score']
            context['last_attempt'] = self.object.quizresult_set.order_by(
                '-completed_at'
            ).first()
        return context

    def delete(self, request, *args, **kwargs):
        response = super().delete(request, *args, **kwargs)
        messages.success(request, 'Quiz deleted successfully.')
        return response



# Add these classes to quiz/admin/views/quiz.py

class QuestionListView(AdminViewMixin, ListView):
    template_name = 'admin/quiz/question_list.html'
    context_object_name = 'questions'
    paginate_by = 10

    def get_queryset(self):
        self.quiz = get_object_or_404(Quiz, pk=self.kwargs['quiz_id'])
        return self.quiz.questions.prefetch_related('answers').all()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['quiz'] = self.quiz
        return context

class QuestionCreateView(AdminViewMixin, CreateView):
    model = Question
    template_name = 'admin/quiz/question_form.html'
    fields = ['text', 'description', 'points']

    def get_quiz(self):
        return get_object_or_404(Quiz, pk=self.kwargs['quiz_id'])

    def form_valid(self, form):
        form.instance.quiz = self.get_quiz()
        response = super().form_valid(form)
        
        # Handle answers
        answer_texts = self.request.POST.getlist('answer_text[]')
        correct_answer = int(self.request.POST.get('correct_answer', 0))
        
        for i, text in enumerate(answer_texts):
            if text.strip():
                Answer.objects.create(
                    question=self.object,
                    text=text,
                    is_correct=(i == correct_answer)
                )
        
        messages.success(self.request, 'Question created successfully.')
        return response

    def get_success_url(self):
        return reverse_lazy('quiz_admin:question_list', kwargs={'quiz_id': self.kwargs['quiz_id']})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['quiz'] = self.get_quiz()
        return context

class QuestionUpdateView(AdminViewMixin, UpdateView):
    model = Question
    template_name = 'admin/quiz/question_form.html'
    fields = ['text', 'description', 'points']

    def form_valid(self, form):
        response = super().form_valid(form)
        
        # Update answers
        existing_answers = {a.id: a for a in self.object.answers.all()}
        updated_answers = set()
        
        answer_texts = self.request.POST.getlist('answer_text[]')
        correct_answer = int(self.request.POST.get('correct_answer', 0))
        
        # Update or create answers
        for i, text in enumerate(answer_texts):
            if text.strip():
                answer_id = self.request.POST.getlist('answer_id[]')[i] if i < len(self.request.POST.getlist('answer_id[]')) else None
                
                if answer_id and answer_id.isdigit() and int(answer_id) in existing_answers:
                    # Update existing answer
                    answer = existing_answers[int(answer_id)]
                    answer.text = text
                    answer.is_correct = (i == correct_answer)
                    answer.save()
                    updated_answers.add(int(answer_id))
                else:
                    # Create new answer
                    Answer.objects.create(
                        question=self.object,
                        text=text,
                        is_correct=(i == correct_answer)
                    )
        
        # Delete answers that weren't updated
        for answer_id in existing_answers:
            if answer_id not in updated_answers:
                existing_answers[answer_id].delete()
        
        messages.success(self.request, 'Question updated successfully.')
        return response

    def get_success_url(self):
        return reverse_lazy('quiz_admin:question_list', kwargs={'quiz_id': self.object.quiz.id})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['quiz'] = self.object.quiz
        context['answers'] = self.object.answers.all()
        return context

class QuestionDeleteView(AdminViewMixin, DeleteView):
    model = Question
    template_name = 'admin/quiz/question_confirm_delete.html'

    def get_success_url(self):
        return reverse_lazy('quiz_admin:question_list', kwargs={'quiz_id': self.object.quiz.id})

    def delete(self, request, *args, **kwargs):
        response = super().delete(request, *args, **kwargs)
        messages.success(request, 'Question deleted successfully.')
        return response

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['quiz'] = self.object.quiz
        return context
