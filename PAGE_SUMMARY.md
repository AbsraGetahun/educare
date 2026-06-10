# EDUCARE – Page Summary & Application Overview

## Application Purpose

**EDUCARE** is an AI-powered mathematics learning support platform built for **Ethiopian secondary students**. It connects four roles — **Students, Teachers, Families, and Administrators** — through a single shared platform. The backend is a **Flask + MySQL** REST API; the frontend is a **React + Tailwind CSS** SPA. JWT handles authentication across all roles.

Key capabilities:
- Role-based login and access (Student / Teacher / Family / Admin)
- Curriculum-aligned quiz taking with automatic scoring and topic mastery tracking
- AI-generated study materials via a RAG pipeline that retrieves context from Ethiopian mathematics textbooks
- Real-time dashboards, progress maps, gap analysis, and performance charts
- Learning gaps waterfall: weak quiz scores → detected gaps → AI-generated practice materials → teacher approval → student consumption

---

## Page-by-Page Capabilities

### 1. `LandingPage` — `/`
**Route:** Landing / home page (public)

The public landing page. Displays:
- A hero section describing the platform with tagline "AI-Powered Mathematics Learning Support"
- A **Choose Your Portal** grid with four role cards:
  - **Student** → `/student/login` (blue theme)
  - **Teacher** → `/teacher/login` (green theme)
  - **Family** → `/family/login` (purple theme)
  - **Administrator** → `/admin/login` (gray theme)
- A **Platform Features** section highlighting interactive quizzes, progress tracking, and AI tutoring
- A **Built for Ethiopia** benefits section
- Footer with quick links to each portal

| What you can do | Detail |
|---|---|
| View the platform | Introduces EDUCARE with stats (1000+ students, 50+ teachers, etc.) |
| Enter a portal | Clicking any role card navigates to the corresponding login page |
| Read features | Static feature highlights and benefit lists |

---

### 2. `StudentLogin` — `/student/login`
**Route:** Student Portal login

Allows existing student accounts to sign in. Uses the shared `/api/login` endpoint; rejects non-student roles after authentication.

| What you can do | Detail |
|---|---|
| Enter email & password | Standard form with validation |
| Get help signing in | Link to `/student/register` |
| Redirect | Successful login → `/student/dashboard` |
| Error feedback | Shows "Access denied. Student account required." if role is not `student` |

---

### 3. `TeacherLogin` — `/teacher/login`
**Route:** Teacher Portal login

Allows existing teacher accounts to sign in. Uses the shared `/api/login` endpoint; rejects non-teacher roles after authentication.

| What you can do | Detail |
|---|---|
| Enter email & password | Same login flow as students |
| Contact admin | "Contact administrator" text shown (teachers are created by admins) |
| Redirect | Successful login → `/teacher/dashboard` |

---

### 4. `FamilyLogin` — `/family/login`
**Route:** Family Portal login

Uses the dedicated `/api/family/login` endpoint. On success, also loads and stores the list of linked students in `localStorage`.

| What you can do | Detail |
|---|---|
| Enter email & password | Family-specific login |
| Get help signing in | Link to `/family/register` |
| Redirect | Successful login → `/family/dashboard` |

---

### 5. `AdminLogin` — `/admin/login`
**Route:** Admin Portal login

Uses the dedicated `/api/admin/login` endpoint with an explicit role check `user[3] != 'admin'`. Admins must be created by a system administrator (SQL script or another admin).

| What you can do | Detail |
|---|---|
| Enter email & password | Admin-specific login |
| Contact admin | "Contact system administrator" text shown |
| Redirect | Successful login → `/admin/dashboard` |

---

### 6. `StudentRegister` — `/student/register`
**Route:** Student self-registration

Allows new students to create an account directly. Validates grade level (9–12) and section. Calls `/api/register` with bcrypt-hashed passwords if available, otherwise plain text (dev fallback). Logs the student in immediately after account creation.

| What you can do | Detail |
|---|---|
| Provide full name | Account holder identification |
| Provide email | Unique identifier; duplicates rejected |
| Provide password | Hashed via bcrypt if installed |
| Select grade level | Dropdown: Grade 9–12 |
| Enter section | Class section (e.g., "A") |
| Account created automatically | Registers user as `role = 'student'` and creates linked `students` row |

---

### 7. `FamilyRegister` — `/family/register`
**Route:** Family self-registration

Creates a family account and simultaneously links it to one student by email. Calls `/api/family/register`.

| What you can do | Detail |
|---|---|
| Provide parent/guardian name | Account holder identification |
| Provide email | Family account email |
| Provide password | Account credential |
| Enter student email | Automatically links the new family account to that student |
| Account created + linked | Roles: `family`; `family` table row records the link |

---

### 8. `StudentDashboard` — `/student/dashboard`
**Route:** Protected; role = `student`

The main student hub with three tabs:

#### Tab — Progress Map
A visual, grade-grouped grid showing every topic and its mastery status:
- **Green (Mastered ≥ 70%)** — topic unlocked, score bar shown
- **Yellow (In Progress)** — some attempts, score below threshold
- **Blue (Available)** — prerequisites met, can be clicked to start a quiz
- **Gray (Locked)** — prerequisites not yet mastered, tooltip shows required topics

#### Tab — Quizzes
Two sections:
- **Recommended for You** — personalized quiz cards surfaced from gap analysis (shows topic, score %, reason, and a Take/Retake button)
- **Available Quizzes** — grouped by topic, filtered by prerequisites met
- **Locked Topics** — shown for transparency when prerequisites block access

#### Tab — Materials
Lists AI-generated study materials approved by teachers. Each material card shows:
- Topic badge, grade, generation date, source citation
- Curriculum context (explanation/formula/examples) rendered as HTML
- Expandable practice questions (with Show/Hide Answer)
- **Download PDF** — opens a print-ready page for the material
- **Practice Mode** — opens an interactive modal with one question at a time, navigation, and a scored results screen
- **Rate this material** — 👍 Helpful / 👎 Not Helpful button pair

#### AI Learning Assistant
A floating chatbot (`StudentAssistant` component) embedded at the bottom of the dashboard that answers math questions with RAG-backed responses.

| What you can do | Detail |
|---|---|
| Visualise mastery | Grade-grouped topic map with locked/available/mastered states |
| Take quizzes | Navigate to `/quiz/:quizId`; submit answers; see score + mastery update |
| View study materials | Browser AI-generated, teacher-approved content with embedded practice questions |
| Practice mode | Modal quiz derived directly from material content |
| Rate materials | Binary helpful/not-helpful rating sent to backend |
| Download material as PDF | Print-to-PDF via browser |
| Chat with AI assistant | Context-aware Q&A backed by curriculum RAG |
| Logout | Clears localStorage and returns to root |

---

### 9. `TeacherDashboard` — `/teacher/dashboard`
**Route:** Protected; role = `teacher`

The teacher operations centre with 9 tabs:

#### Tab — Class Overview
- Summary card with total students, quizzes count, and pending approvals
- **Generate for All Struggling Students** button — batch-generates practice materials for every weak student-topic pair in one bulk operation (grade-level + difficulty selectable)
- Batch progress bar and success/failure summary at the bottom

#### Tab — Mastery Tracker
- Per-topic breakdown showing mastery % across the class
- Expandable rows revealing which students mastered, are in progress, or are struggling on each topic

#### Tab — Curriculum Search
- Keyword search across the 6 Ethiopian textbook PDFs
- Results list with source filename, grade level, page number
- **Generate Material from Result** button — generates a full RAG practice sheet for that topic with one click

#### Tab — Gap Heatmap
- A colour-coded table (good / needs attention / critical) of every topic's class-wide mastery %
- Grade filter (all/9–12) and sort controls (by mastery, by topic name)
- Click-through to see the struggling students for any topic

#### Tab — Students
- List of all students with name, grade, section, and average score
- For each student: input topic + difficulty → **Generate Material** button (targeted, student-specific RAG generation)
- Gap gap colour-coded (High/Moderate/Low) per student

#### Tab — Quizzes
- List of all quizzes with topic, total marks, time limit
- **Create New Quiz** modal — build quizzes question by question (title, topic, time limit, 4-option multiple-choice)
- **Generate AI Quiz** modal — AI generates a full quiz (topic keywords → RAG retrieval → question generation, grade/difficulty selectable)
- Edit / Delete / View Results for existing quizzes
- **Results Modal** — sorted scoreboard per quiz
- Curriculum topic generator — search curriculum by topic to surface context before quiz creation

#### Tab — Pending Approvals
- Cards for all materials awaiting teacher review (title, topic, generation date, source citation)
- **Approve** — moves material to `Approved`, immediately visible to students
- **Reject** — moves material to `Rejected` with one click

#### Tab — Analytics
- **Material Quality & Approval Summary** — total / approved / pending / rejected count
- **Most Generated Topics** — bar chart of generation frequency
- **Topics Students Struggle With Most** — sorted by avg score; one-click Generate Material button on each row
- **Platform Summary** — AI quizzes generated, helpful / not-helpful ratings
- **Batch Material Generation** — generates materials for all weak topics across all students in a grade at once

| What you can do | Detail |
|---|---|
| View class mastery breakdown | Mastery tracker and heatmap tabs |
| Search curriculum | Keyword search across all 6 Ethiopian textbooks via FAISS |
| Create quizzes manually | Full question builder (4-option multiple-choice per quiz) |
| Generate AI-assisted quizzes | RAG-backed quiz generation from curriculum |
| Edit / delete quizzes | Update title, topic, questions, or remove completely |
| View quiz results | Class scoreboard per quiz |
| Generate targeted study materials | Student-specific or topic-generic RAG generation |
| Batch-generate materials | All weak student-topic pairs in one bulk operation |
| Approve / reject materials | Gate AI-generated content before students see it |
| View analytics | Approval stats, top topics, struggling topics, batch generate from analytics |
| Logout | Returns to root |

---

### 10. `FamilyDashboard` — `/family/dashboard`
**Route:** Protected; role = `family`

Family view into a linked student's complete academic record.

- **Child Selector** — dropdown visible when a family account is linked to multiple students
- **Student Info Card** — name, grade, section
- **Performance Trend Chart** — line or bar chart (toggle) of every quiz attempt with:
  - Score % per quiz date
  - Average reference line
  - 70% mastery threshold reference line
  - Custom tooltip on hover (quiz name, topic, date, score)
- **Skill Gaps** — grid of topic gaps with a score bar and High/Moderate/Low badge
- **Recommended Practice** — quiz cards sourced from gap analysis (topic, total marks, current avg score)
- **Download Report** — generates a PDF-style report of the student's complete progress

| What you can do | Detail |
|---|---|
| Switch between linked children | Dropdown selector for multi-child families |
| View performance over time | Line or bar chart (toggle) of quiz scores |
| Identify skill gaps | High/Moderate/Low need cards with avg score bars |
| See recommended practice | Surfaced quizzes from gap analysis |
| Download a performance report | PDF export of full student progress |
| Logout | Returns to `/family/login` |

---

### 11. `AdminDashboard` — `/admin/dashboard`
**Route:** Protected; role = `admin`

System administration panel with a single **User Management** tab.

#### Stats Header
Six cards in one row: Students, Teachers, Families, Admins, Total Quizzes, Average Score

#### User Management Table
- Role filter pills (All / Students / Teachers / Families / Admins)
- Search box (filters by full_name or email)
- **+ Add User** button — opens modal with role-specific fields:
  - Student: name, email, password, grade, section
  - Teacher: name, email, password, qualification, subject
  - Family: name, email, password, relationship (parent/guardian/sibling), student checkbox picker
  - Admin: name, email, password

#### Per-Row Actions
- **Edit** — opens the Edit User modal pre-filled with the user's current data; update sends `PUT /api/admin/user/:id`
- **Delete** — confirmation dialog; confirm sends `DELETE /api/admin/user/:id`

| What you can do | Detail |
|---|---|
| View system stats | Counts of all users by role, quizzes, attempts, avg score |
| View all users | Sortable table with role badges and created dates |
| Filter by role | Quick filter pills for each user type |
| Search users | By name or email |
| Create any user type | Modal with role-conditional fields |
| Edit any user | Update name, email, role, and role-specific fields |
| Delete any user | Confirmation dialog before hard delete |
| Logout | Returns to `/admin/login` |

---

### 12. `QuizTaking` — `/quiz/:quizId`
**Route:** Protected; role = `student`

Interactive quiz interface:

- Loads a full quiz (title, topic, questions) from `/api/quizzes/:id`
- One-question-at-a-time navigation (Previous / Next)
- Multiple-choice selection (A / B / C / D)
- **Submit Quiz** — sends answers to `/api/quizzes/:id/submit`; shows:
  - Raw score and percentage
  - Passed / Keep Practising badge
  - **Topic Mastery card** — average score %, progress bar, and Mastered / X% to master status for the quiz's topic
- **Back to Dashboard** button returns to the student hub

| What you can do | Detail |
|---|---|
| Take a quiz | Loading quiz by topic; one question per screen |
| Navigate questions | Previous / Next arrows; submit only after all answered |
| See instant result | Score, %, pass badge, topic mastery card |
| Retake | Return to dashboard and re-enter the same quiz |

---

## Architecture Summary

| Layer | Tech |
|---|---|
| Backend | Flask (Python), MySQL, Flask-JWT-Extended, FAISS (vector search) |
| Frontend | React, React Router DOM, Axios, Tailwind CSS, Recharts |
| Auth | JWT Bearer tokens stored in `localStorage` |
| RAG / AI | `rag_service.py` queries a FAISS index built from 6 Ethiopian maths textbooks; `question_generator.py` creates 4-option multiple-choice questions per topic; `StudentAssistant.js` answers free-form student questions |
| Gap detection | `gap_utils.py` computes `AVG(score/total_marks)` per student per topic; weakness levels: High (< 40%), Moderate (40–69%), Low (≥ 70%) |
| Material pipeline | Teacher / batch → RAG fetch → question generation → save as `Pending` → teacher approval → `Approved` → student view |

---

## Routing Map

```
/                          → LandingPage
/student/login             → StudentLogin
/student/register          → StudentRegister
/teacher/login             → TeacherLogin
/family/login              → FamilyLogin
/family/register           → FamilyRegister
/admin/login               → AdminLogin
/student/dashboard         → StudentDashboard   (student JWT required)
/teacher/dashboard         → TeacherDashboard   (teacher JWT required)
/family/dashboard          → FamilyDashboard    (family  JWT required)
/admin/dashboard           → AdminDashboard     (admin   JWT required)
/quiz/:quizId              → QuizTaking         (student JWT required)
```
