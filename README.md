# EDUCARE - Mathematics Learning Support Platform

## Overview

EDUCARE is a comprehensive educational platform designed to support mathematics learning for students, teachers, families, and administrators. The platform provides role-based access to track student progress, identify learning gaps, and deliver personalized quiz-based assessments.

## Technology Stack

### Backend
- **Framework**: Flask (Python)
- **Database**: MySQL
- **Authentication**: JWT (JSON Web Tokens) using Flask-JWT-Extended
- **API**: RESTful API endpoints
- **CORS**: Enabled for cross-origin requests

### Frontend
- **Framework**: React.js
- **Routing**: React Router DOM
- **HTTP Client**: Axios
- **Styling**: Tailwind CSS
- **State Management**: React Hooks (useState, useEffect)

## Features

### 1. Student Portal
- **Login**: Secure authentication for students
- **Dashboard**: View available quizzes and track progress
- **Quiz Taking**: Interactive quiz interface with multiple-choice questions
- **Progress Tracking**: View scores and performance history
- **Gap Analysis**: Identify weak areas in mathematics topics

### 2. Teacher Portal
- **Login**: Secure authentication for teachers
- **Dashboard**: Comprehensive overview of student performance
- **Quiz Creation**: Create custom quizzes with configurable parameters
- **Results Analysis**: View detailed quiz results and student performance
- **Student Monitoring**: Track individual student progress

### 3. Family Portal
- **Registration**: Parents/guardians can register and link to student accounts
- **Login**: Secure authentication for family members
- **Dashboard**: Monitor linked students' progress
- **Progress Reports**: View detailed performance metrics for each student
- **Gap Identification**: Identify areas where students need additional support

### 4. Admin Portal
- **Login**: Secure authentication for administrators
- **User Management**: Create, update, and delete user accounts
- **Role Management**: Manage students, teachers, family accounts, and other admins
- **System Statistics**: View overall platform usage and performance metrics
- **Account Linking**: Link family accounts to student accounts

## Database Schema

### Users Table
- `user_id`: Primary key
- `full_name`: User's full name
- `email`: Unique email address
- `password`: User password (stored in plain text for development)
- `role`: User role (student, teacher, family, admin)
- `created_at`: Account creation timestamp

### Students Table
- `user_id`: Foreign key to users table
- `grade_level`: Student's grade level
- `section`: Student's class section
- `enrollment_date`: Date of enrollment

### Teachers Table
- `user_id`: Foreign key to users table
- `qualification`: Teacher's qualifications
- `subject`: Subject taught

### Family Table
- `family_id`: Primary key
- `user_id`: Foreign key to users table (family account)
- `student_id`: Foreign key to users table (linked student)
- `relationship`: Relationship type (e.g., parent, guardian)
- `created_at`: Link creation timestamp

### Quizzes Table
- `quiz_id`: Primary key
- `topic_id`: Foreign key to topics table
- `title`: Quiz title
- `total_marks`: Total possible marks
- `time_limit`: Time limit in minutes
- `created_at`: Quiz creation timestamp

### Topics Table
- `topic_id`: Primary key
- `topic_name`: Name of the mathematics topic
- `grade_level`: Associated grade level

### Quiz Attempts Table
- `attempt_id`: Primary key
- `student_id`: Foreign key to users table
- `quiz_id`: Foreign key to quizzes table
- `score`: Score achieved
- `completed_at`: Completion timestamp

### Results Table
- `result_id`: Primary key
- `student_id`: Foreign key to users table
- `topic_id`: Foreign key to topics table
- `score`: Score achieved
- `assessment_date`: Date of assessment

## API Endpoints

### Authentication
- `POST /api/login` - Student/Teacher login
- `POST /api/register` - Student registration
- `POST /api/family/login` - Family login
- `POST /api/family/register` - Family registration
- `POST /api/admin/login` - Admin login

### Students
- `GET /api/students` - Get all students
- `GET /api/students/:id/attempts` - Get student quiz attempts
- `GET /api/students/:id/gaps` - Get student learning gaps

### Quizzes
- `GET /api/quizzes` - Get all quizzes
- `GET /api/quizzes/:id` - Get quiz details
- `POST /api/quizzes/:id/submit` - Submit quiz answers
- `POST /api/quiz/create` - Create new quiz (teacher only)
- `GET /api/quiz/:id/results` - Get quiz results

### Family
- `GET /api/family/students/list` - Get students available for linking
- `GET /api/family/students` - Get linked students
- `GET /api/family/student/:id/progress` - Get student progress
- `GET /api/family/student/:id/gaps` - Get student gaps
- `GET /api/family/student/:id/recommendations` - Get quiz recommendations

### Admin
- `GET /api/admin/users` - Get all users
- `GET /api/admin/users/:role` - Get users by role
- `POST /api/admin/user` - Create new user
- `PUT /api/admin/user/:id` - Update user
- `DELETE /api/admin/user/:id` - Delete user
- `GET /api/admin/stats` - Get system statistics

## Project Structure

```
educare/
├── educare-backend/
│   ├── app.py                 # Flask backend application
│   ├── requirements.txt       # Python dependencies
│   ├── setup_admin_user.sql   # Admin user setup script
│   └── setup_family_user.sql  # Family user setup script
│
└── educare-frontend/
    ├── public/
    │   ├── index.html
    │   └── ...
    ├── src/
    │   ├── App.js             # Main React application
    │   ├── index.js           # React entry point
    │   ├── pages/
    │   │   ├── Login.js           # Student/Teacher login
    │   │   ├── Register.js        # Student registration
    │   │   ├── StudentDashboard.js
    │   │   ├── TeacherDashboard.js
    │   │   ├── FamilyLogin.js
    │   │   ├── FamilyRegister.js
    │   │   ├── FamilyDashboard.js
    │   │   ├── AdminLogin.js
    │   │   ├── AdminDashboard.js
    │   │   └── QuizTaking.js
    │   └── services/
    │       └── api.js         # API service layer
    ├── package.json
    └── tailwind.config.js
```

## Key Features Implementation

### Role-Based Access Control
The application implements role-based access control using:
- JWT tokens for authentication
- Protected routes in React Router
- Role verification on both frontend and backend

### Learning Gap Analysis
The platform identifies student weaknesses by:
- Tracking quiz scores across different topics
- Calculating average performance per topic
- Categorizing gaps as High, Moderate, or Low priority
- Providing targeted quiz recommendations

### Progress Tracking
Students and families can monitor progress through:
- Historical quiz attempt records
- Score trends over time
- Topic-specific performance metrics
- Visual dashboards with key statistics

### Quiz System
The quiz functionality includes:
- Multiple-choice question format
- Configurable time limits
- Automatic scoring
- Detailed results analysis
- Topic-based categorization

## Security Features

- JWT-based authentication
- Password validation (development mode - plain text)
- Role-based authorization
- CORS configuration for secure cross-origin requests
- Protected API endpoints

## Getting Started

### Backend Setup
1. Install Python dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Configure MySQL database:
   - Create database named `educare`
   - Update database credentials in `app.py`

3. Run the Flask server:
   ```bash
   python app.py
   ```

### Frontend Setup
1. Install Node.js dependencies:
   ```bash
   npm install
   ```

2. Start the React development server:
   ```bash
   npm start
   ```

3. Access the application at `http://localhost:3000`

## User Roles

### Student
- Can take quizzes
- View personal progress
- Access learning gap analysis

### Teacher
- Create and manage quizzes
- View all student results
- Monitor class performance

### Family
- Register and link to student accounts
- Monitor student progress
- View detailed performance reports

### Admin
- Manage all user accounts
- View system statistics
- Configure platform settings

## Future Enhancements

- Password hashing for improved security
- Email verification for account registration
- Advanced analytics and reporting
- Mobile application support
- Real-time notifications
- Automated quiz generation based on learning gaps
- Integration with external learning management systems

## License

This project is developed for educational purposes.

## Support

For issues or questions, please contact the development team.
