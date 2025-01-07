# /quiz/admin/views/category.py

# /quiz/admin/views/category.py
from django.views.generic import ListView, CreateView, UpdateView, DeleteView, View
from django.urls import reverse_lazy
from django.contrib import messages
from django.db.models import Count
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.utils.decorators import method_decorator
from quiz.models import Category
from ..mixins import AdminRequiredMixin
import json

class CategoryListView(AdminRequiredMixin, ListView):
    model = Category
    template_name = 'admin/quiz/category_list.html'
    context_object_name = 'categories'
    paginate_by = 10

    def get_queryset(self):
        queryset = Category.objects.annotate(
            quiz_count=Count('quiz')
        )

        # Handle search
        search_query = self.request.GET.get('search')
        if search_query:
            queryset = queryset.filter(name__icontains=search_query)

        # Handle sorting
        sort_by = self.request.GET.get('sort')
        if sort_by:
            if sort_by == 'name':
                queryset = queryset.order_by('name')
            elif sort_by == 'quiz_count':
                queryset = queryset.order_by('-quiz_count')
            elif sort_by == 'created_at':
                queryset = queryset.order_by('-created_at')
        else:
            queryset = queryset.order_by('name')  # Default sorting

        return queryset

class CategoryCreateView(AdminRequiredMixin, CreateView):
    model = Category
    template_name = 'admin/quiz/category_form.html'
    fields = ['name', 'description', 'icon']
    success_url = reverse_lazy('quiz_admin:category_list')

    def form_valid(self, form):
        messages.success(self.request, 'Category created successfully!')
        return super().form_valid(form)

class CategoryUpdateView(AdminRequiredMixin, UpdateView):
    model = Category
    template_name = 'admin/quiz/category_form.html'
    fields = ['name', 'description', 'icon']
    success_url = reverse_lazy('quiz_admin:category_list')

    def form_valid(self, form):
        messages.success(self.request, 'Category updated successfully!')
        return super().form_valid(form)

class CategoryDeleteView(AdminRequiredMixin, DeleteView):
    model = Category
    template_name = 'admin/quiz/category_confirm_delete.html'
    success_url = reverse_lazy('quiz_admin:category_list')

    def delete(self, request, *args, **kwargs):
        messages.success(request, 'Category deleted successfully!')
        return super().delete(request, *args, **kwargs)

@method_decorator(require_http_methods(['GET', 'PUT', 'DELETE']), name='dispatch')
class CategoryAPIView(AdminRequiredMixin, View):
    def get(self, request, pk):
        try:
            category = Category.objects.get(pk=pk)
            return JsonResponse({
                'id': category.pk,
                'name': category.name,
                'description': category.description,
                'icon': category.icon
            })
        except Category.DoesNotExist:
            return JsonResponse({'error': 'Category not found'}, status=404)

    def put(self, request, pk):
        try:
            category = Category.objects.get(pk=pk)
            data = json.loads(request.body)

            category.name = data.get('name', category.name)
            category.description = data.get('description', category.description)
            category.icon = data.get('icon', category.icon)
            category.save()

            messages.success(request, 'Category updated successfully!')
            return JsonResponse({'status': 'success'})
        except Category.DoesNotExist:
            return JsonResponse({'error': 'Category not found'}, status=404)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)

    def delete(self, request, pk):
        try:
            category = Category.objects.get(pk=pk)
            category.delete()
            messages.success(request, 'Category deleted successfully!')
            return JsonResponse({'status': 'success'})
        except Category.DoesNotExist:
            return JsonResponse({'error': 'Category not found'}, status=404)

@require_http_methods(['POST'])
def category_create_api(request):
    try:
        data = json.loads(request.body)
        category = Category.objects.create(
            name=data['name'],
            description=data.get('description', ''),
            icon=data.get('icon', 'fas fa-folder')
        )
        messages.success(request, 'Category created successfully!')
        return JsonResponse({
            'id': category.pk,
            'name': category.name,
            'description': category.description,
            'icon': category.icon
        }, status=201)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)
