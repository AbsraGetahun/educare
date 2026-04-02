# Mastery-Based Progression System

## What It Does

The Mastery-Based Progression System is a gated learning pathway that requires students to demonstrate competency (70%+ average quiz score) in prerequisite topics before unlocking new ones. It prevents students from advancing to harder material until they have proven understanding of foundational concepts.

## How It Works

### Mastery Calculation

A student's mastery of a topic is determined by the **average percentage score** across all quiz attempts for that topic:

```
Average Score = SUM(quiz_score / total_marks * 100) / number_of_attempts
```

- **Score >= 70%** → Topic is **Mastered**
- **Score < 70%** → Topic is **In Progress**
- **No attempts** → Topic is **Not Started**

### Prerequisite Gating

Each topic in the database has a `prerequisites` field containing comma-separated topic IDs (e.g., `"1,2"` means topics 1 and 2 must be mastered first).

**Rule:** A student cannot access a topic until ALL of its prerequisites are mastered (70%+).

Example dependency chain:
```
Algebra (topic 1) ──┐
                    ├──> Integration (topic 3)
Limits (topic 2) ───┘
```

A student must score 70%+ on both Algebra and Limits quizzes before Integration becomes available.

### Real-Time Updates

When a student submits a quiz, the system:
1. Records the score in `quiz_attempt`
2. Recalculates the average score for that topic
3. Checks if mastery threshold (70%) is now met
4. Returns the updated mastery status in the response
5. Frontend immediately reflects the new status

## Student Dashboard

### Progress Map

A visual grid of all topics grouped by grade level. Each topic card is color-coded:

| Color | Status | Meaning |
|-------|--------|---------|
| Green | Mastered | Average score >= 70% |
| Yellow | In Progress | Some attempts taken, average < 70% |
| Blue | Available | Prerequisites met, no attempts yet |
| Gray | Locked | Prerequisites not met |

Locked topics display a tooltip listing which prerequisite topics must be completed first.

### Quiz Availability

- **Available/In Progress topics:** Show linked quizzes students can take
- **Locked topics:** Appear grayed out with no quiz access
- After completing a quiz, the results screen shows current mastery progress for that topic

## Teacher Dashboard

### Mastery Tracker Tab

An expandable list of all topics showing class-wide statistics:

- **Mastery percentage:** What % of students have mastered this topic
- **Mastered count:** Number of students scoring 70%+
- **Struggling students:** Students who attempted the topic but score below 70%, listed with their average score
- **Blocked students:** Students who haven't started because prerequisites aren't met

### Class Overview Tab

Summary table with:
- Topic name and grade level
- Visual progress bar showing mastery percentage
- Status indicator (Good / Needs Attention / Critical)

## Backend Endpoints

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/student/{id}/available-topics` | GET | All topics with prerequisite status |
| `/api/student/{id}/mastery-status` | GET | Mastery data for every topic |
| `/api/student/{id}/check-mastery/{topic_id}` | POST | Check single topic mastery |
| `/api/student/{id}/progress-map` | GET | Topics grouped by grade with color status |
| `/api/teacher/mastery-overview` | GET | Class-wide mastery with student lists |
| `/api/quizzes/{id}/submit` | POST | Now returns `mastery_update` after submission |

## Database Dependencies

### Topics Table

Requires a `prerequisites` column (TEXT) storing prerequisite topic IDs:

```sql
-- Comma-separated format
UPDATE topics SET prerequisites = '1,2' WHERE topic_id = 3;

-- JSON array format (also supported)
UPDATE topics SET prerequisites = '[1,2]' WHERE topic_id = 3;

-- No prerequisites
UPDATE topics SET prerequisites = NULL WHERE topic_id = 1;
```

### Existing Tables Used

- `topics` — topic definitions with prerequisites
- `quizzes` — quizzes linked to topics via `topic_id`
- `quiz_attempt` — student quiz scores
- `users` — student accounts

## Files Modified

| File | Changes |
|------|---------|
| `educare-backend/app.py` | 6 new endpoints, 4 helper functions, updated quiz submission |
| `educare-frontend/src/services/api.js` | 5 new API functions, updated `getApprovedMaterials` |
| `educare-frontend/src/pages/StudentDashboard.js` | Progress map tab with color-coded topic grid |
| `educare-frontend/src/pages/TeacherDashboard.js` | Mastery tracker tab with expandable topic cards |
| `educare-frontend/src/pages/QuizTaking.js` | Results screen with mastery status display |
