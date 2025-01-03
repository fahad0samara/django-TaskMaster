from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.utils import timezone
from datetime import datetime
import json
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST, require_http_methods
from django.http import JsonResponse, HttpResponse, HttpResponseBadRequest, HttpResponseForbidden
from .models import TodoItem, Category, TodoShare, TodoAttachment, TodoHistory, Tag
from .forms import RegisterForm, TodoForm, ShareTodoForm, TodoAttachmentForm, TodoFilterForm, CustomUserCreationForm
from django.contrib.auth import login, authenticate, logout
from django.contrib import messages
import csv
from datetime import timedelta

def register(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, 'Account created successfully!')
            return redirect('home')
    else:
        form = CustomUserCreationForm()
    
    # Add Bootstrap classes to form fields
    for field in form.fields.values():
        field.widget.attrs['class'] = 'form-control'
        field.widget.attrs['placeholder'] = field.label
    
    return render(request, 'registration/register.html', {'form': form})

def login_view(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('home')
        else:
            messages.error(request, 'Invalid username or password.')
    return render(request, 'registration/login.html')

def logout_view(request):
    logout(request)
    return redirect('home')

@login_required
def home(request):
    return render(request, 'home.html')

@login_required
def todo_detail(request, todo_id):
    todo = get_object_or_404(TodoItem, id=todo_id)
    if not (todo.user == request.user or todo.shared_with.filter(id=request.user.id).exists()):
        return HttpResponseForbidden("You don't have permission to view this todo")
    
    context = {
        'todo': todo,
        'attachment_form': TodoAttachmentForm(),
    }
    return render(request, 'todo_detail.html', context)

@login_required
def complete_todo(request, todo_id):
    todo = get_object_or_404(TodoItem, id=todo_id, user=request.user)
    todo.completed = timezone.now() if not todo.completed else None
    todo.save()
    messages.success(request, 'Todo status updated successfully!')
    return redirect('todo_detail', todo_id=todo.id)

@login_required
def delete_todo(request, todo_id):
    todo = get_object_or_404(TodoItem, id=todo_id, user=request.user)
    todo.delete()
    messages.success(request, 'Todo deleted successfully!')
    return redirect('kanban')

@login_required
def add_subtask(request, todo_id):
    todo = get_object_or_404(TodoItem, id=todo_id)
    if request.method == 'POST':
        title = request.POST.get('title')
        if title:
            subtask = TodoItem.objects.create(
                title=title,
                user=request.user,
                parent=todo,
                category=todo.category
            )
            return JsonResponse({
                'id': subtask.id,
                'title': subtask.title,
                'completed': subtask.completed is not None
            })
    return JsonResponse({'error': 'Invalid request'}, status=400)

@login_required
def add_attachment(request, todo_id):
    todo = get_object_or_404(TodoItem, id=todo_id)
    if request.method == 'POST':
        form = TodoAttachmentForm(request.POST, request.FILES)
        if form.is_valid():
            attachment = form.save(commit=False)
            attachment.todo = todo
            attachment.save()
            messages.success(request, 'Attachment added successfully!')
        else:
            messages.error(request, 'Error adding attachment.')
    return redirect('todo_detail', todo_id=todo.id)

@login_required
def manage_categories(request):
    categories = Category.objects.filter(user=request.user)
    if request.method == 'POST':
        name = request.POST.get('name')
        color = request.POST.get('color')
        Category.objects.create(name=name, color=color, user=request.user)
        messages.success(request, 'Category created successfully!')
        return redirect('manage_categories')
    return render(request, 'categories.html', {'categories': categories})

@login_required
def share_todo(request, todo_id):
    todo = get_object_or_404(TodoItem, id=todo_id, user=request.user)
    if request.method == 'POST':
        form = ShareTodoForm(request.POST)
        if form.is_valid():
            share = form.save(commit=False)
            share.todo = todo
            share.shared_by = request.user
            share.save()
            messages.success(request, 'Todo shared successfully!')
            return redirect('todo_detail', todo_id=todo.id)
    else:
        form = ShareTodoForm()
    return render(request, 'share_todo.html', {'form': form, 'todo': todo})

@login_required
def kanban(request):
    todos = TodoItem.objects.filter(
        Q(user=request.user) | Q(shared_with=request.user)
    ).filter(parent__isnull=True)
    return render(request, 'kanban.html', {'todos': todos})

@login_required
@require_POST
def update_todo_status(request):
    try:
        data = json.loads(request.body)
        todo_id = data.get('taskId')
        new_status = data.get('newStatus')
        
        if not todo_id or not new_status:
            return JsonResponse({'error': 'Missing required fields'}, status=400)
        
        todo = get_object_or_404(TodoItem, id=todo_id)
        if todo.user != request.user:
            return JsonResponse({'error': 'Permission denied'}, status=403)
        
        # Update status
        todo.status = new_status
        if new_status == 'completed':
            todo.completed = timezone.now()
        else:
            todo.completed = None
        todo.save()
        
        # Create history entry
        TodoHistory.objects.create(
            todo=todo,
            user=request.user,
            action=f"Changed status to {new_status}"
        )
        
        return JsonResponse({
            'message': 'Status updated successfully',
            'status': new_status,
            'completed': todo.completed is not None
        })
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)

@login_required
@require_POST
def create_todo(request):
    try:
        data = json.loads(request.body)
        title = data.get('title')
        description = data.get('description')
        category_id = data.get('category')
        due_date = data.get('dueDate')
        status = data.get('status', 'todo')
        
        if not title:
            return JsonResponse({'error': 'Title is required'}, status=400)
        
        todo = TodoItem(
            title=title,
            description=description,
            user=request.user,
            status=status
        )
        
        if category_id:
            category = get_object_or_404(Category, id=category_id, user=request.user)
            todo.category = category
        
        if due_date:
            todo.due_date = datetime.strptime(due_date, '%Y-%m-%d').date()
        
        todo.save()
        
        # Create history entry
        TodoHistory.objects.create(
            todo=todo,
            user=request.user,
            action="Created todo"
        )
        
        return JsonResponse({
            'id': todo.id,
            'title': todo.title,
            'description': todo.description,
            'category': todo.category.name if todo.category else None,
            'categoryColor': todo.category.color if todo.category else None,
            'dueDate': todo.due_date.strftime('%Y-%m-%d') if todo.due_date else None,
            'status': todo.status,
            'completed': todo.completed is not None
        })
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)

@login_required
def edit_todo(request, todo_id):
    todo = get_object_or_404(TodoItem, id=todo_id, user=request.user)
    
    try:
        data = json.loads(request.body)
        title = data.get('title')
        description = data.get('description')
        category_id = data.get('category')
        due_date = data.get('dueDate')
        
        if title:
            todo.title = title
        if description:
            todo.description = description
        
        if category_id:
            category = get_object_or_404(Category, id=category_id, user=request.user)
            todo.category = category
        
        if due_date:
            todo.due_date = datetime.strptime(due_date, '%Y-%m-%d').date()
        
        todo.save()
        
        # Create history entry
        TodoHistory.objects.create(
            todo=todo,
            user=request.user,
            action="Updated todo"
        )
        
        return JsonResponse({
            'message': 'Todo updated successfully',
            'todo': {
                'id': todo.id,
                'title': todo.title,
                'description': todo.description,
                'category': todo.category.name if todo.category else None,
                'categoryColor': todo.category.color if todo.category else None,
                'dueDate': todo.due_date.strftime('%Y-%m-%d') if todo.due_date else None,
                'status': todo.status,
                'completed': todo.completed is not None
            }
        })
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)

@login_required
def calendar_view(request):
    """Calendar view showing todos by due date"""
    todos = TodoItem.objects.filter(
        Q(user=request.user) | Q(shared_with=request.user)
    ).filter(due_date__isnull=False)
    
    # Convert todos to calendar events
    events = []
    for todo in todos:
        # Set event color based on priority
        priority_class = {
            'high': 'priority-high',
            'medium': 'priority-medium',
            'low': 'priority-low'
        }.get(todo.priority, 'priority-low')
        
        # Format the event
        event = {
            'id': str(todo.id),
            'title': todo.title,
            'start': todo.due_date.isoformat(),
            'end': (todo.due_date + timedelta(hours=1)).isoformat(),
            'description': todo.description,
            'priority': todo.priority,
            'category': todo.category.id if todo.category else None,
            'className': priority_class,
            'allDay': False,
        }
        events.append(event)
    
    # Get categories for the form
    categories = Category.objects.filter(user=request.user)
    
    context = {
        'events': json.dumps(events),
        'categories': categories,
        'current_time': timezone.now().isoformat(),
    }
    return render(request, 'calendar.html', context)

def email_preview(request, template):
    """Preview email templates (development only)"""
    if not request.user.is_superuser:
        return redirect('home')
    
    context = {
        'user': request.user,
        'todo': TodoItem.objects.filter(user=request.user).first(),
        'site_url': request.build_absolute_uri('/'),
    }
    
    template_map = {
        'welcome': 'email/welcome.html',
        'task_reminder': 'email/task_reminder.html',
    }
    
    template_name = template_map.get(template)
    if not template_name:
        messages.error(request, 'Template not found')
        return redirect('home')
    
    return render(request, template_name, context)

def about(request):
    """Public about page - only for non-authenticated users"""
    if request.user.is_authenticated:
        return redirect('kanban')
    return render(request, 'about.html')

def features(request):
    """Public features page - only for non-authenticated users"""
    if request.user.is_authenticated:
        return redirect('kanban')
    return render(request, 'features.html')

def contact(request):
    """Public contact page - only for non-authenticated users"""
    if request.user.is_authenticated:
        return redirect('kanban')
    if request.method == 'POST':
        name = request.POST.get('name')
        email = request.POST.get('email')
        message = request.POST.get('message')
        # Add your contact form processing logic here
        messages.success(request, 'Your message has been sent successfully!')
        return redirect('contact')
    return render(request, 'contact.html')

@login_required
def export_todos(request, format):
    todos = TodoItem.objects.filter(user=request.user)
    if format == 'csv':
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="todos.csv"'
        writer = csv.writer(response)
        writer.writerow(['Title', 'Description', 'Due Date', 'Status', 'Category'])
        for todo in todos:
            writer.writerow([
                todo.title,
                todo.description,
                todo.due_date,
                todo.status,
                todo.category.name if todo.category else ''
            ])
        return response
    elif format == 'json':
        data = []
        for todo in todos:
            data.append({
                'title': todo.title,
                'description': todo.description,
                'due_date': str(todo.due_date) if todo.due_date else None,
                'status': todo.status,
                'category': todo.category.name if todo.category else None
            })
        response = HttpResponse(json.dumps(data), content_type='application/json')
        response['Content-Disposition'] = 'attachment; filename="todos.json"'
        return response
    return redirect('kanban')
