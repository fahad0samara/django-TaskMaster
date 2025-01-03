from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    # Authentication URLs
    path('', views.home, name='home'),
    path('register/', views.register, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    
    # Todo Management URLs
    path('todo/create/', views.create_todo, name='create_todo'),
    path('todo/<int:todo_id>/edit/', views.edit_todo, name='edit_todo'),
    path('todo/<int:todo_id>/delete/', views.delete_todo, name='delete_todo'),
    path('todo/<int:todo_id>/share/', views.share_todo, name='share_todo'),
    path('todo/<int:todo_id>/add-subtask/', views.add_subtask, name='add_subtask'),
    path('todo/<int:todo_id>/add-attachment/', views.add_attachment, name='add_attachment'),
    path('todo/<int:todo_id>/', views.todo_detail, name='todo_detail'),
    path('todo/<int:todo_id>/complete/', views.complete_todo, name='complete_todo'),
    
    # Category Management
    path('categories/', views.manage_categories, name='manage_categories'),
    
    # Calendar View
    path('calendar/', views.calendar_view, name='calendar'),
    
    # Kanban Board
    path('kanban/', views.kanban, name='kanban'),
    path('todo/update_status/', views.update_todo_status, name='update_todo_status'),
    
    # Export Features
    path('export/<str:format>/', views.export_todos, name='export_todos'),
    
    # Public Pages (for non-authenticated users)
    path('about/', views.about, name='about'),
    path('features/', views.features, name='features'),
    path('contact/', views.contact, name='contact'),
    
    # Email Preview (for development)
    path('email/preview/<str:template>/', views.email_preview, name='email_preview'),
]
