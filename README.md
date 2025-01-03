# TaskMaster - Modern Task Management System

TaskMaster is a feature-rich task management system built with Django that helps users organize, track, and collaborate on tasks effectively. With its modern interface and comprehensive feature set, it's perfect for both personal task management and team collaboration.

## 🌟 Features

### Task Management
- **Kanban Board**: Drag-and-drop interface for managing tasks across different stages
- **Calendar View**: Visual calendar interface for deadline tracking
- **Categories**: Organize tasks with custom categories
- **Subtasks**: Break down complex tasks into manageable subtasks
- **Attachments**: Add files and documents to tasks
- **Task History**: Track changes and updates to tasks

### Collaboration
- **Task Sharing**: Share tasks with team members
- **Permission Control**: Manage view and edit permissions for shared tasks
- **Email Notifications**: Automated notifications for task updates and deadlines

### User Experience
- **Modern UI**: Clean and intuitive interface with responsive design
- **Quick Actions**: Easily create, edit, and complete tasks
- **Search & Filter**: Find tasks quickly with advanced filtering options
- **Export**: Export tasks to CSV format for reporting

## 🚀 Getting Started

### Prerequisites
- Python 3.8 or higher
- pip (Python package manager)
- Virtual environment (recommended)

### Installation

1. Clone the repository:
```bash
git clone [repository-url]
cd project
```

2. Create and activate a virtual environment:
```bash
python -m venv venv
# On Windows:
venv\Scripts\activate
# On Unix or MacOS:
source venv/bin/activate
```

3. Install required packages:
```bash
pip install -r requirements.txt
```

4. Apply database migrations:
```bash
python manage.py migrate
```

5. Create a superuser (admin):
```bash
python manage.py createsuperuser
```

6. Run the development server:
```bash
python manage.py runserver
```

The application will be available at `http://localhost:8000`

## 🔧 Configuration

### Environment Variables
Create a `.env` file in the project root with the following variables:
```env
DEBUG=True
SECRET_KEY=your-secret-key
DATABASE_URL=sqlite:///db.sqlite3
EMAIL_HOST=smtp.your-email-provider.com
EMAIL_PORT=587
EMAIL_HOST_USER=your-email@example.com
EMAIL_HOST_PASSWORD=your-email-password
EMAIL_USE_TLS=True
```

### Email Configuration
The system uses email for:
- Welcome emails for new users
- Task reminders
- Due date notifications
- Share notifications

## 📱 Usage

### Task Management
1. **Creating Tasks**:
   - Click the "+" button on the Kanban board
   - Fill in task details (title, description, due date, category)
   - Add attachments or subtasks if needed

2. **Managing Tasks**:
   - Drag tasks between columns on the Kanban board
   - Click on a task to view/edit details
   - Use the calendar view for deadline management

3. **Sharing Tasks**:
   - Open a task and click "Share"
   - Enter the username/email of the team member
   - Set appropriate permissions

### Categories
1. Access category management from the sidebar
2. Create, edit, or delete categories
3. Assign colors for visual organization

### Calendar View
1. Switch to calendar view from the sidebar
2. View tasks by their due dates
3. Click on dates to create or view tasks

## 🔒 Security

- CSRF protection enabled
- Password hashing using Django's auth system
- Secure file handling for attachments
- Permission-based access control

## 🛠 Development

### Project Structure
```
project/
├── manage.py
├── project/
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
└── myapp/
    ├── models.py
    ├── views.py
    ├── forms.py
    ├── urls.py
    └── templates/
```

### Key Components
- **Models**: Task, Category, Share, Attachment, History
- **Views**: Task management, user authentication, API endpoints
- **Templates**: Modern, responsive interface using Bootstrap

## 📝 Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 👥 Authors

- [Your Name/Team Name]

## 🙏 Acknowledgments

- Django Framework
- Bootstrap for UI components
- Font Awesome for icons
