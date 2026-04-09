import axios from 'axios';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:5000';

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

// Quiz APIs
export const getQuizzes = async () => {
  const response = await api.get('/api/quizzes');
  return response.data;
};

export const getQuizById = async (quizId) => {
  const response = await api.get(`/api/quizzes/${quizId}`);
  return response.data;
};

export const submitQuiz = async (quizId, studentId, answers) => {
  const response = await api.post(`/api/quizzes/${quizId}/submit`, {
    student_id: studentId,
    answers
  });
  return response.data;
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
  const response = await api.get(`/api/family/students/${studentId}/progress`);
  return response.data;
};

export const getFamilyStudentGaps = async (studentId) => {
  const response = await api.get(`/api/family/students/${studentId}/gaps`);
  return response.data;
};

export const getFamilyStudentRecommendations = async (studentId) => {
  const response = await api.get(`/api/family/students/${studentId}/recommendations`);
  return response.data;
};

export const getStudentReport = async (studentId) => {
  const response = await api.get(`/api/family/students/${studentId}/report`, {
    responseType: 'blob'
  });
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
  const response = await api.post('/api/teacher/quizzes', quizData);
  return response.data;
};

export const getQuizResults = async (quizId) => {
  const response = await api.get(`/api/teacher/quizzes/${quizId}/results`);
  return response.data;
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
export const getStudents = async () => {
  const response = await api.get('/api/students');
  return response.data;
};

export const getPendingMaterials = async () => {
  const response = await api.get('/api/materials/pending');
  return response.data;
};

export const approveMaterial = async (materialId) => {
  const response = await api.post(`/api/materials/approve/${materialId}`);
  return response.data;
};

export const rejectMaterial = async (materialId) => {
  const response = await api.post(`/api/materials/reject/${materialId}`);
  return response.data;
};

// Student Materials APIs
export const getApprovedMaterials = async (studentId) => {
  try {
    const params = studentId ? { student_id: studentId } : {};
    const response = await api.get('/api/student/materials', { params });
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
export const getTeacherMasteryOverview = async () => {
  const response = await api.get('/api/teacher/mastery-overview');
  return response.data;
};

// Teacher Heatmap API
export const getHeatmap = async () => {
  const response = await api.get('/api/teacher/heatmap');
  return response.data;
};

// RAG Material Generation API
export const generatePracticeMaterial = async (topicName, studentId, difficulty = 'medium') => {
  const response = await api.post('/api/materials/generate', {
    topic_name: topicName,
    student_id: studentId,
    difficulty
  });
  return response.data;
};

export default api;
