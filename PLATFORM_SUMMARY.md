# EDUCARE - Platform Capabilities Summary

## Project Overview
EDUCARE is a comprehensive mathematics learning support platform with role-based dashboards for Students, Teachers, Families, and Administrators. The platform enables quiz-based assessments, progress tracking, learning gap analysis, and AI-powered material generation.

---

## Dashboard Capabilities

### 1. Student Dashboard (`StudentDashboard.js`)

**Purpose:** Individual learning experience for students

**Core Features:**
- **Progress Map** - Visual topic progression showing mastery status (Mastered/In Progress/Available/Locked)
- **Quiz Taking** - Interactive multiple-choice quizzes with timed assessments
- **Materials Library** - Access AI-generated practice materials with embedded questions
- **Personalized Recommendations** - Quiz suggestions based on learning gaps

**Technical Capabilities:**
- Automatic prerequisite checking to unlock topics
- Score threshold detection (70%+ = mastered)
- Progress color coding (green/yellow/blue/gray)
- Quiz attempt history tracking
- Material content parsing with interactive question components

**Tabs:**
- Progress Map - Topic-by-topic mastery visualization
- Quizzes - Available quizzes with status indicators
- Materials - RAG-generated practice content

---

### 2. Teacher Dashboard (`TeacherDashboard.js`)

**Purpose:** Class management and student monitoring for educators

**Core Features:**
- **Class Overview** - Stats cards showing total students, quizzes, pending approvals
- **Mastery Tracker** - Expandable topic sections showing struggling/blocked students
- **Gap Heatmap** - Visual grid of class performance across all topics
- **Student Management** - Individual student profiles with skill gap analysis
- **Quiz Management** - Create, view results, and manage quizzes
- **Material Approvals** - Review and approve/reject AI-generated materials
- **Curriculum Search** - Search educational content from curriculum database

**Teacher Actions:**
- Create new quizzes (title, topic, marks, time limit)
- View quiz results with student scores
- Approve or reject pending materials
- Generate practice materials for specific students
- Filter heatmap by grade level or mastery percentage

**Tabs:**
- Class Overview - Summary stats + topic mastery table
- Mastery Tracker - Expandable student breakdown per topic
- Curriculum Search - Search across curriculum PDFs
- Gap Heatmap - Visual class performance grid
- Students - Student list with skill gaps + material generation
- Quizzes - Quiz cards with results view
- Pending Approvals - Material review workflow

---

### 3. Family Dashboard (`FamilyDashboard.js`)

**Purpose:** Parent/guardian monitoring of linked student(s)

**Core Features:**
- **Multi-Student Support** - Switch between linked students
- **Progress Charts** - Line and bar charts showing score trends over time
- **Gap Analysis** - Identify weak areas categorized by severity (High/Moderate/Low)
- **Recommendations** - Suggested quizzes for improvement
- **PDF Reports** - Downloadable performance reports

**Visualization:**
- Line chart: Quiz scores over time
- Bar chart: Performance by topic
- Pie chart: Mastery distribution
- Gap severity badges (color-coded)

**Actions:**
- Select linked student from dropdown
- Toggle between chart types (line/bar)
- Download PDF progress report

---

### 4. Admin Dashboard (`AdminDashboard.js`)

**Purpose:** System-wide user and content management

**Core Features:**
- **User Management** - CRUD operations for all user types
- **Role-Based Filtering** - View users by role (student/teacher/family/admin)
- **Search Functionality** - Search by name or email
- **Statistics Overview** - Dashboard stats showing user counts and quiz metrics

**Admin Stats Displayed:**
- Total Students
- Total Teachers
- Total Families
- Total Admins
- Total Quizzes
- Average Score

**User Management Actions:**
- Add new user (with role-specific fields)
- Edit existing user
- Delete user (with confirmation modal)
- Filter by role
- Search users

**Role-Specific Fields:**
- Students: Grade Level, Section
- Teachers: Qualification, Subject
- Families: Relationship (parent/guardian/sibling), Linked Students

---

## API Endpoints Summary

### Authentication
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/login` | POST | Student/Teacher login |
| `/api/register` | POST | Student registration |
| `/api/admin/login` | POST | Admin login |
| `/api/family/login` | POST | Family login |
| `/api/family/register` | POST | Family registration |

### Student APIs
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/students` | GET | Get all students |
| `/api/student/{id}/available-topics` | GET | Get unlockable topics |
| `/api/student/{id}/mastery-status` | GET | Get topic mastery |
| `/api/student/{id}/progress-map` | GET | Get progress visualization |
| `/api/student/{id}/check-mastery/{topic}` | POST | Check topic mastery |
| `/api/student/{id}/gaps` | GET | Get learning gaps |
| `/api/student/{id}/recommendations` | GET | Get quiz recommendations |
| `/api/student/{id}/completed-quizzes` | GET | Get completed quizzes |

### Teacher APIs
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/teacher/mastery-overview` | GET | Class mastery summary |
| `/api/teacher/heatmap` | GET | Class performance heatmap |
| `/api/materials/pending` | GET | Get pending materials |
| `/api/materials/approve/{id}` | POST | Approve material |
| `/api/materials/reject/{id}` | POST | Reject material |
| `/api/materials/generate` | POST | Generate new material |

### Family APIs
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/family/students` | GET | Get linked students |
| `/api/family/student/{id}/progress` | GET | Get student progress |
| `/api/family/student/{id}/gaps` | GET | Get student gaps |
| `/api/family/student/{id}/recommendations` | GET | Get recommendations |

### Admin APIs
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/admin/users` | GET | Get all users |
| `/api/admin/users/{role}` | GET | Get users by role |
| `/api/admin/user` | POST | Create user |
| `/api/admin/user/{id}` | PUT | Update user |
| `/api/admin/user/{id}` | DELETE | Delete user |
| `/api/admin/stats` | GET | Get system statistics |

### Quiz APIs
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/quizzes` | GET | Get all quizzes |
| `/api/quiz/{id}` | GET | Get quiz details |
| `/api/quiz/{id}/submit` | POST | Submit quiz answers |
| `/api/quiz/{id}/results` | GET | Get quiz results |
| `/api/quiz/create` | POST | Create new quiz |

### Curriculum APIs
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/curriculum/search` | GET | Search curriculum |
| `/api/student/materials` | GET | Get approved materials |

---

## Technology Stack

### Backend
- **Framework:** Flask (Python)
- **Database:** MySQL
- **Authentication:** JWT (Flask-JWT-Extended)
- **AI Integration:** RAG (Retrieval-Augmented Generation) for material generation

### Frontend
- **Framework:** React.js
- **Styling:** Tailwind CSS
- **Charts:** Recharts
- **Routing:** React Router DOM

---

## Key Features

### 1. Mastery-Based Progression
- Students must score 70%+ to master a topic
- Prerequisites must be mastered to unlock new topics
- Visual progress map shows status for each topic

### 2. Learning Gap Analysis
- Automatic detection of weak areas
- Categorization: High/Moderate/Low priority
- Targeted quiz recommendations

### 3. AI Material Generation
- RAG-based curriculum search
- Automatic question generation
- Teacher approval workflow

### 4. Multi-Role Support
- 4 distinct user types with tailored dashboards
- Role-based access control
- Family linking to multiple students

---

## Database Schema

### Core Tables
- **users** - All user accounts (students, teachers, families, admins)
- **students** - Student-specific data (grade, section)
- **teachers** - Teacher-specific data (qualification, subject)
- **family** - Family links to students
- **topics** - Mathematics topics with prerequisites
- **quizzes** - Quiz definitions
- **quiz_attempt** - Student quiz attempts with scores
- **material** - AI-generated learning materials
- **quiz_questions** - Quiz question options

---

## Frontend Pages

| Page | Purpose |
|------|---------|
| LandingPage.js | Marketing page with feature overview |
| StudentLogin.js | Student authentication |
| StudentRegister.js | Student self-registration |
| StudentDashboard.js | Student learning hub |
| TeacherLogin.js | Teacher authentication |
| TeacherDashboard.js | Teacher class management |
| FamilyLogin.js | Family authentication |
| FamilyRegister.js | Family registration with student linking |
| FamilyDashboard.js | Family student monitoring |
| AdminLogin.js | Admin authentication |
| AdminDashboard.js | Admin user management |
| QuizTaking.js | Interactive quiz interface |

---

## Recent Fixes Applied

1. **Teacher Dashboard API Errors** - Fixed 422/500 errors on mastery-overview, heatmap, materials/pending endpoints by removing JWT requirements and adding error handling
2. **Material Approval** - Fixed approve/reject endpoints to work without JWT
3. **Layout Redesign** - Applied compact professional styling to all dashboards
4. **Automatic Data Loading** - Ensured all dashboards load data on mount