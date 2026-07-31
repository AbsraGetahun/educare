import axios from 'axios';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'https://educare-docker.onrender.com';
const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});
// Add token to requests if available
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Auth APIs
export const login = async (email, password) => {
  const response = await api.post('/api/login', { email, password });
  return response.data;
};

export const register = async (userData) => {
  const response = await api.post('/api/register', userData);
  return response.data;
};

export const adminLogin = async (email, password) => {
  const response = await api.post('/api/admin/login', { email, password });
  return response.data;
};

export const familyLogin = async (email, password) => {
  const response = await api.post('/api/family/login', { email, password });
  return response.data;
};

export const familyRegister = async (fullName, email, password, studentEmail, relationship = 'parent') => {
  const response = await api.post('/api/family/register', {
    full_name: fullName,
    email,
    password,
    student_email: studentEmail,
    relationship
  });
  return response.data;
};

export const listLinkableStudents = async () => {
  const response = await api.get('/api/family/students/list');
  return response.data;
};

// Quiz APIs
export const getQuizzes = async () => {
  try {
    const response = await api.get('/api/quizzes');
    return response.data;
  } catch (err) {
    console.error('Error fetching quizzes:', err);
    return { quizzes: [] };
  }
};

export const getQuizById = async (quizId) => {
  const response = await api.get(`/api/quizzes/${quizId}`);
  return response.data;
};

export const submitQuiz = async (quizId, studentId, answers) => {
  try {
    const response = await api.post(`/api/quizzes/${quizId}/submit`, {
      student_id: studentId,
      answers
    });
    return response.data;
  } catch (err) {
    console.error('Error submitting quiz:', err);
    return { error: err.response?.data?.error || 'Failed to submit quiz', score: 0 };
  }
};

// Student APIs
export const getStudentProgress = async (studentId) => {
  const response = await api.get(`/api/students/${studentId}/progress`);
  return response.data;
};

export const getStudentGaps = async (studentId) => {
  const response = await api.get(`/api/students/${studentId}/gaps`);
  return response.data;
};

// Family APIs
export const getFamilyStudents = async () => {
  const response = await api.get('/api/family/students');
  return response.data;
};

export const getFamilyStudentProgress = async (studentId) => {
  const response = await api.get(`/api/family/student/${studentId}/progress`);
  return response.data;
};

export const getFamilyStudentGaps = async (studentId) => {
  const response = await api.get(`/api/family/student/${studentId}/gaps`);
  return response.data;
};

export const getFamilyStudentRecommendations = async (studentId) => {
  const response = await api.get(`/api/family/student/${studentId}/recommendations`);
  return response.data;
};

export const getStudentReport = async (studentId) => {
  const response = await api.get(`/api/family/student/${studentId}/report`, {
    responseType: 'blob',
  });
  const contentType = response.headers['content-type'] || '';
  if (contentType.includes('application/json')) {
    const text = await response.data.text();
    let message = 'Failed to generate report';
    try {
      const err = JSON.parse(text);
      message = err.error || message;
    } catch (_) { /* use default */ }
    throw new Error(message);
  }
  return response.data;
};

// Teacher APIs
export const getTeacherStudents = async () => {
  const response = await api.get('/api/teacher/students');
  return response.data;
};

export const getTeacherQuizzes = async () => {
  const response = await api.get('/api/teacher/quizzes');
  return response.data;
};

export const createQuiz = async (quizData) => {
  try {
    const response = await api.post('/api/quiz/create', quizData);
    return response.data;
  } catch (err) {
    console.error('Error creating quiz:', err);
    return { error: err.message, quiz_id: null };
  }
};

export const updateQuiz = async (quizId, quizData) => {
  try {
    const response = await api.put(`/api/quiz/${quizId}`, quizData);
    return response.data;
  } catch (err) {
    console.error('Error updating quiz:', err);
    return { error: err.message };
  }
};

export const deleteQuiz = async (quizId) => {
  try {
    const response = await api.delete(`/api/quiz/${quizId}`);
    return response.data;
  } catch (err) {
    console.error('Error deleting quiz:', err);
    return { error: err.message };
  }
};

export const getQuizResults = async (quizId) => {
  try {
    const response = await api.get(`/api/quiz/${quizId}/results`);
    return response.data;
  } catch (err) {
    console.error('Error fetching quiz results:', err);
    return { results: [], error: err.message };
  }
};

// Admin APIs
export const getAdminStats = async () => {
  const response = await api.get('/api/admin/stats');
  return response.data;
};

export const getAdminUsers = async () => {
  const response = await api.get('/api/admin/users');
  return response.data;
};

export const getAdminQuizzes = async () => {
  const response = await api.get('/api/admin/quizzes');
  return response.data;
};

export const approveQuiz = async (quizId) => {
  const response = await api.post(`/api/admin/quizzes/${quizId}/approve`);
  return response.data;
};

export const rejectQuiz = async (quizId) => {
  const response = await api.post(`/api/admin/quizzes/${quizId}/reject`);
  return response.data;
};

// Admin User Management APIs
export const adminGetUsers = async () => {
  const response = await api.get('/api/admin/users');
  return response.data;
};

export const adminGetStats = async () => {
  const response = await api.get('/api/admin/stats');
  return response.data;
};

export const adminGetUsersByRole = async (role) => {
  const response = await api.get(`/api/admin/users/${role}`);
  return response.data;
};

export const adminCreateUser = async (userData) => {
  const response = await api.post('/api/admin/user', userData);
  return response.data;
};

export const adminUpdateUser = async (userId, userData) => {
  const response = await api.put(`/api/admin/user/${userId}`, userData);
  return response.data;
};

export const adminDeleteUser = async (userId) => {
  const response = await api.delete(`/api/admin/user/${userId}`);
  return response.data;
};

// Curriculum Search API
export const searchCurriculum = async (query) => {
  const response = await api.get('/api/curriculum/search', { params: { q: query } });
  return response.data;
};

// Teacher Materials APIs
export const getStudents = async (gradeLevel) => {
  const params = {};
  if (gradeLevel != null && gradeLevel !== '') {
    params.grade_level = gradeLevel;
  }
  const response = await api.get('/api/students', { params });
  return response.data;
};

export const getPendingMaterials = async () => {
  const response = await api.get('/api/materials/pending');
  return response.data;
};

export const assignMaterialToStudent = async (materialId, studentId) => {
  const response = await api.post(`/api/materials/${materialId}/assign`, {
    student_id: studentId,
  });
  return response.data;
};

export const approveMaterial = async (materialId, studentId = null) => {
  const payload = studentId ? { student_id: studentId } : {};
  const response = await api.post(`/api/materials/approve/${materialId}`, payload);
  return response.data;
};

export const rejectMaterial = async (materialId) => {
  const response = await api.post(`/api/materials/reject/${materialId}`);
  return response.data;
};

// Student Materials APIs
export const getApprovedMaterials = async (studentId) => {
  try {
    const response = await api.get('/api/student/materials', {
      params: { student_id: studentId },
    });
    return response.data;
  } catch (err) {
    console.error('Error fetching materials:', err);
    return { materials: [] };
  }
};

export const getStudentRecommendations = async (studentId) => {
  try {
    const response = await api.get(`/api/student/${studentId}/recommendations`);
    return response.data;
  } catch (err) {
    console.error('Error fetching recommendations:', err);
    return { recommendations: [] };
  }
};

export const getCompletedQuizzes = async (studentId) => {
  try {
    const response = await api.get(`/api/student/${studentId}/completed-quizzes`);
    return response.data;
  } catch (err) {
    console.error('Error fetching completed quizzes:', err);
    return { completed_quizzes: {} };
  }
};

// Mastery-Based Progression APIs
export const getAvailableTopics = async (studentId) => {
  try {
    const response = await api.get(`/api/student/${studentId}/available-topics`);
    return response.data;
  } catch (err) {
    console.error('Error fetching available topics:', err);
    return { topics: [] };
  }
};

export const getMasteryStatus = async (studentId) => {
  try {
    const response = await api.get(`/api/student/${studentId}/mastery-status`);
    return response.data;
  } catch (err) {
    console.error('Error fetching mastery status:', err);
    return { status: {} };
  }
};

export const checkMastery = async (studentId, topicId) => {
  try {
    const response = await api.post(`/api/student/${studentId}/check-mastery/${topicId}`);
    return response.data;
  } catch (err) {
    console.error('Error checking mastery:', err);
    return { mastered: false };
  }
};

export const getProgressMap = async (studentId) => {
  try {
    const response = await api.get(`/api/student/${studentId}/progress-map`);
    return response.data;
  } catch (err) {
    console.error('Error fetching progress map:', err);
    return { progress_map: {}, grades: [] };
  }
};

// Teacher Mastery Overview API
export const getTeacherMasteryOverview = async (gradeLevel) => {
  const params = {};
  if (gradeLevel != null && gradeLevel !== '') {
    params.grade_level = gradeLevel;
  }
  const response = await api.get('/api/teacher/mastery-overview', { params });
  return response.data;
};

// Teacher Heatmap API
export const getHeatmap = async (gradeLevel) => {
  const params = {};
  if (gradeLevel != null && gradeLevel !== '') {
    params.grade_level = gradeLevel;
  }
  const response = await api.get('/api/teacher/heatmap', { params });
  return response.data;
};

// RAG Material Generation API
export const generatePracticeMaterial = async (topicName, studentId, difficulty = 'medium', skipDedup = false, teacherId, teacherGrade) => {
  const payload = {
    topic_name: topicName,
    student_id: studentId,
    difficulty,
    skip_dedup: skipDedup,
  };
  if (teacherId) payload.teacher_id = teacherId;
  if (teacherGrade != null && teacherGrade !== '') payload.teacher_grade_level = teacherGrade;
  const response = await api.post('/api/materials/generate', payload);
  return response.data;
};

// Topic-based Material Generation API
export const generateMaterialByTopic = async (
  topicName,
  gradeLevel,
  difficulty = 'medium',
  teacherId,
  studentId = null,
  { forAllStudents = false } = {}
) => {
  const payload = {
    topic_name: topicName,
    grade_level: gradeLevel,
    difficulty,
  };
  if (teacherId) payload.teacher_id = teacherId;
  if (forAllStudents) {
    payload.for_all_students = true;
  } else if (studentId) {
    payload.student_id = studentId;
  }
  const response = await api.post('/api/materials/generate', payload);
  return response.data;
};

// Curriculum search by topic API
export const searchCurriculumByTopic = async (topicName, gradeLevel) => {
  const response = await api.post('/api/curriculum/search-by-topic', {
    topic_name: topicName,
    grade_level: gradeLevel
  });
  return response.data;
};

// ── New: AI Quiz Generation (RAG-backed) ─────────────────────────
export const generateAIQuiz = async (data) => {
  const response = await api.post('/api/quiz/generate-ai', data);
  return response.data;
};

// ── New: AI Student Assistant Chatbot ─────────────────────────────
export const askAssistant = async (question, studentId) => {
  const response = await api.post('/api/assistant/ask', {
    question,
    student_id: studentId,
  });
  return response.data;
};

export const getAssistantHistory = async (studentId) => {
  const response = await api.get(`/api/assistant/history/${studentId}`);
  return response.data;
};

export const clearAssistantHistory = async (studentId) => {
  const response = await api.request({ method: 'DELETE', url: '/api/assistant/history', data: { student_id: studentId } });
  return response.data;
};

// ── New: Batch Material Generation ────────────────────────────────
export const generateBatchMaterials = async (data) => {
  const response = await api.post('/api/materials/generate-batch', data);
  return response.data;
};

// ── New: Material Analytics ───────────────────────────────────────
export const getMaterialsAnalytics = async (gradeLevel, teacherId) => {
  const params = {};
  if (gradeLevel != null && gradeLevel !== '') params.grade_level = gradeLevel;
  if (teacherId) params.teacher_id = teacherId;
  const response = await api.get('/api/materials/analytics', { params });
  return response.data;
};

// ── New: Curriculum topic suggestions (autocomplete) ──────────────
export const getCurriculumTopics = async (prefixed) => {
  const response = await api.get('/api/curriculum/topics', {
    params: prefixed ? { prefix: prefixed } : {},
  });
  return response.data;
};

// ── New: Student rates material ───────────────────────────────────
export const rateMaterial = async (materialId, rating, studentId) => {
  const response = await api.post(`/api/materials/${materialId}/rate`, {
    rating,
    student_id: studentId,
  });
  return response.data;
};

// ── File uploads ────────────────────────────────────────────────────
export const uploadFile = async (file, context = 'peer') => {
  const form = new FormData();
  form.append('file', file);
  form.append('context', context);
  const response = await api.post('/api/upload', form, {
    headers: { 'Content-Type': 'multipart/form-data' },
  });
  return response.data;
};

// ── Peer-to-peer student questions ────────────────────────────────
export const postPeerQuestion = async (studentId, questionText, attachments = []) => {
  const response = await api.post('/api/peer/questions', {
    student_id: studentId,
    question_text: questionText,
    attachments,
  });
  return response.data;
};

export const getPeerQuestionFeed = async (studentId) => {
  const response = await api.get('/api/peer/questions', {
    params: { student_id: studentId },
  });
  return response.data;
};

export const getMyPeerQuestions = async (studentId) => {
  const response = await api.get('/api/peer/my-questions', {
    params: { student_id: studentId },
  });
  return response.data;
};

export const postPeerAnswer = async (questionId, studentId, answerText, attachments = []) => {
  const response = await api.post(`/api/peer/questions/${questionId}/answers`, {
    student_id: studentId,
    answer_text: answerText,
    attachments,
  });
  return response.data;
};

// ===== NEW: Email Verification + Auth Flow =====
export const verifyEmail = async (token) => {
  const response = await api.get(`/api/verify-email?token=${encodeURIComponent(token)}`);
  return response.data;
};

export const forgotPassword = async (email) => {
  const response = await api.post('/api/forgot-password', { email });
  return response.data;
};

export const resetPassword = async (email, otp, new_password) => {
  const response = await api.post('/api/reset-password', { email, otp, new_password });
  return response.data;
};

// ===== NEW: Profile APIs =====
export const getProfile = async () => {
  const response = await api.get('/api/profile');
  return response.data;
};

export const updateProfile = async (full_name, email) => {
  const response = await api.put('/api/profile', { full_name, email });
  return response.data;
};

export const changePassword = async (old_password, new_password, confirm_password) => {
  const response = await api.put('/api/profile/password', {
    old_password,
    new_password,
    confirm_password,
  });
  return response.data;
};

export const uploadProfilePicture = async (file) => {
  const form = new FormData();
  form.append('file', file);
  const response = await api.post('/api/profile/picture', form, {
    headers: { 'Content-Type': 'multipart/form-data' },
  });
  return response.data;
};

export default api;
