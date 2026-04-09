import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { getQuizzes, getStudents, getStudentGaps, getQuizResults, createQuiz, updateQuiz, deleteQuiz, getPendingMaterials, approveMaterial, rejectMaterial, getTeacherMasteryOverview, getHeatmap, searchCurriculum, generatePracticeMaterial } from '../services/api';

function TeacherDashboard() {
  const [activeTab, setActiveTab] = useState('overview');
  const [quizzes, setQuizzes] = useState([]);
  const [students, setStudents] = useState([]);
  const [selectedStudent, setSelectedStudent] = useState(null);
  const [studentGaps, setStudentGaps] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [showCreateQuiz, setShowCreateQuiz] = useState(false);
  const [showEditQuiz, setShowEditQuiz] = useState(false);
  const [editingQuiz, setEditingQuiz] = useState(null);
  const [selectedQuizResults, setSelectedQuizResults] = useState(null);
  const [showResultsModal, setShowResultsModal] = useState(false);
  const [pendingMaterials, setPendingMaterials] = useState([]);
  const [showRejectConfirm, setShowRejectConfirm] = useState(null);
  const [masteryOverview, setMasteryOverview] = useState([]);
  const [totalStudents, setTotalStudents] = useState(0);
  const [expandedTopic, setExpandedTopic] = useState(null);
  const [heatmapData, setHeatmapData] = useState([]);
  const [heatmapGradeFilter, setHeatmapGradeFilter] = useState('all');
  const [heatmapSort, setHeatmapSort] = useState('mastery');
  const [selectedHeatmapTopic, setSelectedHeatmapTopic] = useState(null);
  const [curriculumQuery, setCurriculumQuery] = useState('');
  const [curriculumResults, setCurriculumResults] = useState([]);
  const [curriculumLoading, setCurriculumLoading] = useState(false);
  const [curriculumSearched, setCurriculumSearched] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [generateTopic, setGenerateTopic] = useState('');
  const [generateDifficulty, setGenerateDifficulty] = useState('medium');
  const [generateStatus, setGenerateStatus] = useState('');
  const [isGenerating, setIsGenerating] = useState(false);
  const [newQuiz, setNewQuiz] = useState({
    title: '',
    topic_id: '',
    total_marks: '',
    time_limit: '30',
    questions: []
  });
  const [quizForm, setQuizForm] = useState({
    title: '',
    topic_id: '',
    total_marks: '',
    time_limit: '30',
    questions: []
  });
  const [newQuestion, setNewQuestion] = useState({
    question_text: '',
    option_a: '',
    option_b: '',
    option_c: '',
    option_d: '',
    correct_answer: 'A'
  });
  const navigate = useNavigate();
  const fullName = localStorage.getItem('full_name');

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    setLoading(true);
    try {
      const [quizzesData, studentsData, materialsData, masteryData, heatmapResult] = await Promise.all([
        getQuizzes(),
        getStudents(),
        getPendingMaterials(),
        getTeacherMasteryOverview(),
        getHeatmap()
      ]);
      setQuizzes(quizzesData.quizzes || []);
      setStudents(studentsData.students || []);
      setPendingMaterials(materialsData.materials || []);
      setMasteryOverview(masteryData.overview || []);
      setTotalStudents(masteryData.total_students || 0);
      setHeatmapData(heatmapResult.heatmap || []);
    } catch (err) {
      setError('Failed to load data');
    } finally {
      setLoading(false);
    }
  };

  const fetchStudentGaps = async (studentId) => {
    try {
      const gapsData = await getStudentGaps(studentId);
      setStudentGaps(gapsData.gaps || []);
    } catch (err) {
      console.error('Failed to load gaps');
    }
  };

  const handleStudentSelect = (student) => {
    setSelectedStudent(student);
    fetchStudentGaps(student.user_id);
  };

  const handleViewQuizResults = async (quiz) => {
    try {
      const results = await getQuizResults(quiz.quiz_id);
      setSelectedQuizResults({ quiz, results: results.results || [] });
      setShowResultsModal(true);
    } catch (err) {
      alert('Failed to load quiz results');
    }
  };

  const handleCreateQuiz = async (e) => {
    e.preventDefault();
    if (!quizForm.title || !quizForm.topic_id) {
      alert('Please fill title and select a topic');
      return;
    }

    try {
      const payload = {
        title: quizForm.title,
        topic_id: parseInt(quizForm.topic_id),
        total_marks: quizForm.total_marks || quizForm.questions.length,
        time_limit: quizForm.time_limit || 30,
        questions: quizForm.questions
      };
      const result = await createQuiz(payload);
      if (result.quiz_id) {
        alert(`Quiz created successfully with ${quizForm.questions.length} questions!`);
      } else {
        alert('Quiz created but may have errors: ' + (result.error || ''));
      }
      setShowCreateQuiz(false);
      setQuizForm({ title: '', topic_id: '', total_marks: '', time_limit: '30', questions: [] });
      fetchData();
    } catch (err) {
      alert('Failed to create quiz');
    }
  };

  const handleAddQuestion = () => {
    if (!newQuestion.question_text || !newQuestion.option_a || !newQuestion.option_b) {
      alert('Please fill in question text and at least two options');
      return;
    }
    setQuizForm({
      ...quizForm,
      questions: [...quizForm.questions, { ...newQuestion }]
    });
    setNewQuestion({
      question_text: '',
      option_a: '',
      option_b: '',
      option_c: '',
      option_d: '',
      correct_answer: 'A'
    });
  };

  const handleRemoveQuestion = (index) => {
    setQuizForm({
      ...quizForm,
      questions: quizForm.questions.filter((_, i) => i !== index)
    });
  };

  const handleApproveMaterial = async (materialId) => {
    try {
      await approveMaterial(materialId);
      setPendingMaterials(pendingMaterials.filter(m => m.material_id !== materialId));
      alert('Material approved successfully!');
    } catch (err) {
      alert('Failed to approve material');
    }
  };

  const handleEditQuiz = (quiz) => {
    setEditingQuiz(quiz);
    setQuizForm({
      title: quiz.title,
      topic_id: quiz.topic_id || '',
      total_marks: quiz.total_marks || '',
      time_limit: quiz.time_limit || '30',
      questions: quiz.questions || []
    });
    setShowEditQuiz(true);
  };

  const handleUpdateQuiz = async () => {
    if (!editingQuiz) return;
    try {
      const payload = {
        title: quizForm.title,
        topic_id: parseInt(quizForm.topic_id),
        total_marks: quizForm.total_marks || quizForm.questions.length,
        time_limit: quizForm.time_limit || 30,
        questions: quizForm.questions
      };
      await updateQuiz(editingQuiz.quiz_id, payload);
      alert('Quiz updated successfully!');
      setShowEditQuiz(false);
      setEditingQuiz(null);
      setQuizForm({ title: '', topic_id: '', total_marks: '', time_limit: '30', questions: [] });
      fetchData();
    } catch (err) {
      alert('Failed to update quiz');
    }
  };

  const handleRejectMaterial = async (materialId) => {
    try {
      await rejectMaterial(materialId);
      setPendingMaterials(pendingMaterials.filter(m => m.material_id !== materialId));
      setShowRejectConfirm(null);
      alert('Material rejected successfully!');
    } catch (err) {
      alert('Failed to reject material');
    }
  };

  const handleLogout = () => {
    localStorage.clear();
    navigate('/login');
  };

  const handleCurriculumSearch = async (e) => {
    e.preventDefault();
    if (!curriculumQuery.trim()) return;
    setCurriculumLoading(true);
    setCurriculumSearched(true);
    try {
      const data = await searchCurriculum(curriculumQuery);
      setCurriculumResults(data.results || []);
    } catch (err) {
      setCurriculumResults([]);
    } finally {
      setCurriculumLoading(false);
    }
  };

  const handleSearch = async () => {
    if (!searchQuery.trim()) return;
    setIsLoading(true);
    try {
      const data = await searchCurriculum(searchQuery);
      setSearchResults(data.results || []);
    } catch (err) {
      setSearchResults([]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleGenerateMaterial = async () => {
    if (!generateTopic || !selectedStudent) return;
    setIsGenerating(true);
    setGenerateStatus('');
    try {
      await generatePracticeMaterial(generateTopic, selectedStudent.user_id, generateDifficulty);
      setGenerateStatus('success');
      const materialsData = await getPendingMaterials();
      setPendingMaterials(materialsData.materials || []);
    } catch (err) {
      setGenerateStatus('error');
    } finally {
      setIsGenerating(false);
    }
  };

  const getWeaknessColor = (level) => {
    if (level === 'High') return 'bg-red-100 text-red-800';
    if (level === 'Moderate') return 'bg-yellow-100 text-yellow-800';
    return 'bg-green-100 text-green-800';
  };

  const getMasteryBarColor = (pct) => {
    if (pct >= 70) return 'bg-green-500';
    if (pct >= 40) return 'bg-yellow-500';
    return 'bg-red-500';
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-100">
        <div className="text-center">
          <div className="text-xl text-gray-600">Loading dashboard...</div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-100" style={{ backgroundColor: '#f3f4f6' }}>
      {/* Navigation Bar */}
      <nav className="bg-white shadow-sm sticky top-0 z-10" style={{ backgroundColor: '#ffffff' }}>
        <div className="max-w-7xl mx-auto px-4">
          <div className="flex justify-between items-center py-3">
            <div className="flex items-center gap-4">
              <h1 className="text-lg font-bold" style={{ color: '#2563eb' }}>EDUCARE</h1>
              <span className="text-gray-400">|</span>
              <span className="text-gray-600 text-sm">Teacher Portal</span>
            </div>
            <div className="flex items-center gap-4">
              <span className="text-gray-600 text-sm">Welcome, {fullName}</span>
              <button
                onClick={handleLogout}
                className="px-3 py-1.5 text-sm rounded-md transition"
                style={{ backgroundColor: '#ef4444', color: 'white' }}
              >
                Logout
              </button>
            </div>
          </div>
        </div>
      </nav>

      {/* Tabs */}
      <div className="bg-white border-b" style={{ backgroundColor: '#ffffff' }}>
        <div className="max-w-7xl mx-auto">
          <div className="flex gap-2">
            <button
              onClick={() => setActiveTab('overview')}
              className={`py-2 px-4 text-sm font-medium transition ${
                activeTab === 'overview'
                  ? 'border-b-2'
                  : 'text-gray-500 hover:text-gray-700'
              }`}
              style={activeTab === 'overview' ? { borderColor: '#2563eb', color: '#2563eb' } : {}}
            >
              Class Overview
            </button>
            <button
              onClick={() => setActiveTab('mastery')}
              className={`py-2 px-4 text-sm font-medium transition ${
                activeTab === 'mastery'
                  ? 'border-b-2'
                  : 'text-gray-500 hover:text-gray-700'
              }`}
              style={activeTab === 'mastery' ? { borderColor: '#2563eb', color: '#2563eb' } : {}}
            >
              Mastery Tracker
            </button>
            <button
              onClick={() => setActiveTab('curriculum')}
              className={`py-2 px-4 text-sm font-medium transition ${
                activeTab === 'curriculum'
                  ? 'border-b-2'
                  : 'text-gray-500 hover:text-gray-700'
              }`}
              style={activeTab === 'curriculum' ? { borderColor: '#2563eb', color: '#2563eb' } : {}}
            >
              Curriculum Search
            </button>
            <button
              onClick={() => setActiveTab('heatmap')}
              className={`py-2 px-4 text-sm font-medium transition ${
                activeTab === 'heatmap'
                  ? 'border-b-2'
                  : 'text-gray-500 hover:text-gray-700'
              }`}
              style={activeTab === 'heatmap' ? { borderColor: '#2563eb', color: '#2563eb' } : {}}
            >
              Gap Heatmap
            </button>
            <button
              onClick={() => setActiveTab('students')}
              className={`py-2 px-4 text-sm font-medium transition ${
                activeTab === 'students'
                  ? 'border-b-2'
                  : 'text-gray-500 hover:text-gray-700'
              }`}
              style={activeTab === 'students' ? { borderColor: '#2563eb', color: '#2563eb' } : {}}
            >
              Students
            </button>
            <button
              onClick={() => setActiveTab('quizzes')}
              className={`py-2 px-4 text-sm font-medium transition ${
                activeTab === 'quizzes'
                  ? 'border-b-2'
                  : 'text-gray-500 hover:text-gray-700'
              }`}
              style={activeTab === 'quizzes' ? { borderColor: '#2563eb', color: '#2563eb' } : {}}
            >
              Quizzes
            </button>
            <button
              onClick={() => setActiveTab('approvals')}
              className={`py-2 px-4 text-sm font-medium transition ${
                activeTab === 'approvals'
                  ? 'border-b-2'
                  : 'text-gray-500 hover:text-gray-700'
              }`}
              style={activeTab === 'approvals' ? { borderColor: '#2563eb', color: '#2563eb' } : {}}
            >
              Pending Approvals ({pendingMaterials.length})
            </button>
          </div>
        </div>
      </div>

      {/* Content */}
      <div className="max-w-7xl mx-auto px-4 py-4">
        {error && (
          <div className="mb-4 px-4 py-3 rounded" style={{ backgroundColor: '#fef2f2', color: '#991b1b', border: '1px solid #fecaca' }}>
            {error}
          </div>
        )}

        {/* Overview Tab */}
        {activeTab === 'overview' && (
          <div>
            <h2 className="text-xl font-bold mb-4">Class Overview</h2>
            
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-4">
              <div className="bg-white rounded-lg shadow-sm p-4" style={{ backgroundColor: '#ffffff' }}>
                <div className="text-2xl font-bold" style={{ color: '#2563eb' }}>{students.length}</div>
                <div className="text-xs text-gray-500 uppercase">Total Students</div>
              </div>
              <div className="bg-white rounded-lg shadow-sm p-4" style={{ backgroundColor: '#ffffff' }}>
                <div className="text-2xl font-bold" style={{ color: '#10b981' }}>{quizzes.length}</div>
                <div className="text-xs text-gray-500 uppercase">Active Quizzes</div>
              </div>
              <div className="bg-white rounded-lg shadow-sm p-4" style={{ backgroundColor: '#ffffff' }}>
                <div className="text-2xl font-bold" style={{ color: '#f59e0b' }}>{pendingMaterials.length}</div>
                <div className="text-xs text-gray-500 uppercase">Pending Approvals</div>
              </div>
            </div>

            {/* Quick Mastery Summary */}
            <div className="bg-white rounded-lg shadow-sm p-4 mb-4" style={{ backgroundColor: '#ffffff' }}>
              <h3 className="text-base font-semibold mb-3">Topic Mastery Summary</h3>
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="border-b">
                      <th className="text-left py-2">Topic</th>
                      <th className="text-left py-2">Grade</th>
                      <th className="text-left py-2">Mastery %</th>
                      <th className="text-left py-2">Mastered</th>
                      <th className="text-left py-2">Status</th>
                    </tr>
                  </thead>
                  <tbody>
                    {masteryOverview.map((topic) => (
                      <tr key={topic.topic_id} className="border-b even:bg-gray-50">
                        <td className="py-2">{topic.topic_name}</td>
                        <td className="py-2">{topic.grade_level}</td>
                        <td className="py-2">
                          <div className="flex items-center gap-2">
                            <div className="w-24 bg-gray-200 rounded-full h-2">
                              <div
                                className="h-2 rounded-full"
                                style={{ width: `${topic.mastery_pct}%`, backgroundColor: topic.mastery_pct >= 70 ? '#10b981' : topic.mastery_pct >= 40 ? '#f59e0b' : '#ef4444' }}
                              ></div>
                            </div>
                            <span className="text-sm">{topic.mastery_pct}%</span>
                          </div>
                        </td>
                        <td className="py-2">{topic.mastered_count}/{topic.total_students}</td>
                        <td className="py-2">
                          <span className={`px-2 py-1 rounded text-xs ${
                            topic.mastery_pct >= 70 ? 'bg-green-100 text-green-800' :
                            topic.mastery_pct >= 40 ? 'bg-yellow-100 text-yellow-800' :
                            'bg-red-100 text-red-800'
                          }`}>
                            {topic.mastery_pct >= 70 ? 'Good' : topic.mastery_pct >= 40 ? 'Needs Attention' : 'Critical'}
                          </span>
                        </td>
                      </tr>
                    ))}
                    {masteryOverview.length === 0 && (
                      <tr>
                        <td colSpan="5" className="py-8 text-center text-gray-500">No topic data available</td>
                      </tr>
                    )}
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        )}

        {/* Mastery Tracker Tab */}
        {activeTab === 'mastery' && (
          <div>
            <h2 className="text-xl font-bold mb-2">Mastery Tracker</h2>
            <p className="text-gray-600 mb-3 text-sm">Click on a topic to view students who need remediation or are blocked by prerequisites.</p>

            <div className="space-y-3">
              {masteryOverview.map((topic) => (
                <div key={topic.topic_id} className="bg-white rounded-lg shadow-sm overflow-hidden" style={{ backgroundColor: '#ffffff' }}>
                  <button
                    onClick={() => setExpandedTopic(expandedTopic === topic.topic_id ? null : topic.topic_id)}
                    className="w-full p-3 flex justify-between items-center hover:bg-gray-50 transition"
                  >
                    <div className="flex items-center gap-3">
                      <div className="w-10 h-10 rounded-lg flex items-center justify-center text-white font-bold text-sm"
                        style={{ backgroundColor: topic.mastery_pct >= 70 ? '#10b981' : topic.mastery_pct >= 40 ? '#f59e0b' : '#ef4444' }}>
                        {topic.mastery_pct}%
                      </div>
                      <div className="text-left">
                        <h3 className="font-medium text-sm">{topic.topic_name}</h3>
                        <p className="text-xs text-gray-500">Grade {topic.grade_level} - {topic.mastered_count} of {topic.total_students} students mastered</p>
                      </div>
                    </div>
                    <div className="flex items-center gap-2">
                      {topic.struggling_students.length > 0 && (
                        <span className="bg-red-100 text-red-800 px-2 py-0.5 rounded text-xs">
                          {topic.struggling_students.length} struggling
                        </span>
                      )}
                      {topic.blocked_students.length > 0 && (
                        <span className="bg-gray-100 text-gray-800 px-2 py-0.5 rounded text-xs">
                          {topic.blocked_students.length} blocked
                        </span>
                      )}
                      <span className="text-gray-400 text-xs">{expandedTopic === topic.topic_id ? '▲' : '▼'}</span>
                    </div>
                  </button>

                  {expandedTopic === topic.topic_id && (
                    <div className="border-t p-3 bg-gray-50">
                      <div className="mb-3">
                        <div className="flex justify-between text-xs mb-1">
                          <span>Class Mastery</span>
                          <span>{topic.mastered_count}/{topic.total_students} students ({topic.mastery_pct}%)</span>
                        </div>
                        <div className="w-full bg-gray-200 rounded-full h-2">
                          <div
                            className="h-2 rounded-full"
                            style={{ width: `${topic.mastery_pct}%`, backgroundColor: topic.mastery_pct >= 70 ? '#10b981' : topic.mastery_pct >= 40 ? '#f59e0b' : '#ef4444' }}
                          ></div>
                        </div>
                      </div>

                      <div className="grid md:grid-cols-2 gap-3">
                        <div>
                          <h4 className="font-medium mb-2 text-red-700 text-sm">Needs Remediation</h4>
                          {topic.struggling_students.length > 0 ? (
                            <div className="space-y-1">
                              {topic.struggling_students.map((student) => (
                                <div key={student.student_id} className="flex justify-between items-center bg-white rounded p-2 border text-sm">
                                  <span>{student.full_name}</span>
                                  <span className="text-red-600 font-medium">{student.avg_score}%</span>
                                </div>
                              ))}
                            </div>
                          ) : (
                            <p className="text-sm text-gray-500 bg-white rounded p-2 border">No struggling students</p>
                          )}
                        </div>

                        <div>
                          <h4 className="font-medium mb-2 text-gray-700 text-sm">Blocked by Prerequisites</h4>
                          {topic.blocked_students.length > 0 ? (
                            <div className="space-y-1">
                              {topic.blocked_students.map((student) => (
                                <div key={student.student_id} className="flex justify-between items-center bg-white rounded p-2 border text-sm">
                                  <span>{student.full_name}</span>
                                  <span className="text-gray-500">Not started</span>
                                </div>
                              ))}
                            </div>
                          ) : (
                            <p className="text-sm text-gray-500 bg-white rounded p-2 border">No blocked students</p>
                          )}
                        </div>
                      </div>
                    </div>
                  )}
                </div>
              ))}

              {masteryOverview.length === 0 && (
                <div className="bg-white rounded-lg shadow-sm p-8 text-center">
                  <p className="text-gray-500">No mastery data available</p>
                </div>
              )}
            </div>
          </div>
        )}

        {/* Gap Heatmap Tab */}
        {activeTab === 'heatmap' && (
          <div>
            <h2 className="text-xl font-bold mb-2">Class-wide Gap Heatmap</h2>
            <p className="text-gray-600 mb-3 text-sm">Visual overview of class performance across all topics. Click a topic to view struggling students.</p>

            <div className="flex flex-wrap gap-3 mb-4">
              <div>
                <label className="block text-xs font-medium text-gray-700 mb-1">Filter by Grade</label>
                <select
                  value={heatmapGradeFilter}
                  onChange={(e) => setHeatmapGradeFilter(e.target.value)}
                  className="border rounded px-2 py-1.5 text-sm focus:outline-none focus:ring-2"
                  style={{ borderColor: '#d1d5db' }}
                >
                  <option value="all">All Grades</option>
                  {[...new Set(heatmapData.map(t => t.grade_level))].sort().map(g => (
                    <option key={g} value={g}>Grade {g}</option>
                  ))}
                </select>
              </div>
              <div>
                <label className="block text-xs font-medium text-gray-700 mb-1">Sort by</label>
                <select
                  value={heatmapSort}
                  onChange={(e) => setHeatmapSort(e.target.value)}
                  className="border rounded px-2 py-1.5 text-sm focus:outline-none focus:ring-2"
                  style={{ borderColor: '#d1d5db' }}
                >
                  <option value="mastery">Mastery % (Low to High)</option>
                  <option value="mastery_desc">Mastery % (High to Low)</option>
                  <option value="name">Topic Name (A-Z)</option>
                  <option value="grade">Grade Level</option>
                </select>
              </div>
            </div>

            <div className="flex gap-4 mb-4 flex-wrap">
              <div className="flex items-center gap-1.5">
                <div className="w-3 h-3 rounded" style={{ backgroundColor: '#10b981' }}></div>
                <span className="text-xs text-gray-600">Good (70%+)</span>
              </div>
              <div className="flex items-center gap-1.5">
                <div className="w-3 h-3 rounded" style={{ backgroundColor: '#f59e0b' }}></div>
                <span className="text-xs text-gray-600">Needs Attention (40-69%)</span>
              </div>
              <div className="flex items-center gap-1.5">
                <div className="w-3 h-3 rounded" style={{ backgroundColor: '#ef4444' }}></div>
                <span className="text-xs text-gray-600">Critical (below 40%)</span>
              </div>
            </div>

            {(() => {
              let filtered = [...heatmapData];
              if (heatmapGradeFilter !== 'all') {
                filtered = filtered.filter(t => t.grade_level === parseInt(heatmapGradeFilter));
              }
              if (heatmapSort === 'mastery') {
                filtered.sort((a, b) => a.mastery_percentage - b.mastery_percentage);
              } else if (heatmapSort === 'mastery_desc') {
                filtered.sort((a, b) => b.mastery_percentage - a.mastery_percentage);
              } else if (heatmapSort === 'name') {
                filtered.sort((a, b) => a.topic_name.localeCompare(b.topic_name));
              } else if (heatmapSort === 'grade') {
                filtered.sort((a, b) => a.grade_level - b.grade_level || a.topic_name.localeCompare(b.topic_name));
              }

              if (filtered.length === 0) {
                return (
                  <div className="bg-white rounded-lg shadow-sm p-8 text-center">
                    <p className="text-gray-500">No topics match the selected filter</p>
                  </div>
                );
              }

              return (
                <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-3">
                  {filtered.map((topic) => {
                    const statusColor = topic.status === 'good' ? '#10b981' : topic.status === 'needs_attention' ? '#f59e0b' : '#ef4444';
                    const statusLabel = topic.status === 'good' ? 'Good' : topic.status === 'needs_attention' ? 'Needs Attention' : 'Critical';
                    const statusBg = topic.status === 'good' ? 'bg-green-100 text-green-800' : topic.status === 'needs_attention' ? 'bg-yellow-100 text-yellow-800' : 'bg-red-100 text-red-800';
                    return (
                      <button
                        key={topic.topic_id}
                        onClick={() => setSelectedHeatmapTopic(topic)}
                        className="bg-white rounded-lg shadow-sm p-3 text-left hover:shadow-md transition border-t-2"
                        style={{ borderTopColor: statusColor, backgroundColor: '#ffffff' }}
                        title={`${topic.mastered_count} mastered, ${topic.struggling_count} struggling, ${topic.untouched_count} not started`}
                      >
                        <div className="flex justify-between items-start mb-2">
                          <div>
                            <h3 className="font-medium text-sm text-gray-800">{topic.topic_name}</h3>
                            <p className="text-xs text-gray-500">Grade {topic.grade_level}</p>
                          </div>
                          <span className={`text-xs px-1.5 py-0.5 rounded font-medium ${statusBg}`}>
                            {statusLabel}
                          </span>
                        </div>
                        <div className="mb-2">
                          <span className="text-xl font-bold" style={{ color: statusColor }}>
                            {topic.mastery_percentage}%
                          </span>
                          <span className="text-xs text-gray-500 ml-1">mastery</span>
                        </div>
                        <div className="w-full bg-gray-200 rounded-full h-1.5 mb-2">
                          <div
                            className="h-1.5 rounded-full transition-all"
                            style={{ width: `${topic.mastery_percentage}%`, backgroundColor: statusColor }}
                          ></div>
                        </div>
                        <div className="flex justify-between text-xs text-gray-500">
                          <span title="Mastered">{topic.mastered_count} mastered</span>
                          <span title="Struggling">{topic.struggling_count} struggling</span>
                          <span title="Not started">{topic.untouched_count} not started</span>
                        </div>
                      </button>
                    );
                  })}
                </div>
              );
            })()}
          </div>
        )}

        {/* Curriculum Search Tab */}
        {activeTab === 'curriculum' && (
          <div>
            <h2 className="text-xl font-bold mb-3">Curriculum Search</h2>
            <div className="flex gap-2 mb-4">
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                onKeyDown={(e) => e.key === 'Enter' && handleSearch()}
                placeholder="Search curriculum..."
                className="flex-1 px-3 py-1.5 text-sm border rounded-lg focus:outline-none focus:ring-2"
                style={{ borderColor: '#d1d5db' }}
              />
              <button
                onClick={handleSearch}
                className="px-3 py-1.5 text-sm rounded-lg transition text-white"
                style={{ backgroundColor: '#2563eb' }}
              >
                Search
              </button>
            </div>

            {isLoading && (
              <div className="text-center py-6">
                <div className="text-gray-500">Searching...</div>
              </div>
            )}

            {!isLoading && searchResults.length > 0 && (
              <div className="space-y-3">
                {searchResults.map((result, idx) => (
                  <div key={idx} className="bg-white rounded-lg shadow-sm p-3" style={{ backgroundColor: '#ffffff' }}>
                    <p className="text-gray-700 mb-2 text-sm">
                      {result.text ? result.text.substring(0, 300) : 'No preview available'}
                      {result.text && result.text.length > 300 ? '...' : ''}
                    </p>
                    <div className="flex gap-3 text-xs text-gray-500">
                      {result.source_pdf && (
                        <span>Source: {result.source_pdf}</span>
                      )}
                      {result.page_number && (
                        <span>Page: {result.page_number}</span>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            )}

            {!isLoading && searchResults.length === 0 && searchQuery && (
              <div className="bg-white rounded-lg shadow-sm p-6 text-center">
                <p className="text-gray-500">No results found</p>
              </div>
            )}
          </div>
        )}

        {/* Students Tab */}
        {activeTab === 'students' && (
          <div>
            <h2 className="text-xl font-bold mb-3">Student Management</h2>
            
            <div className="grid md:grid-cols-3 gap-3">
              <div className="bg-white rounded-lg shadow-sm p-3" style={{ backgroundColor: '#ffffff' }}>
                <h3 className="font-medium mb-2 text-sm">Students</h3>
                <div className="space-y-1 max-h-80 overflow-y-auto">
                  {students.map((student) => (
                    <button
                      key={student.user_id}
                      onClick={() => handleStudentSelect(student)}
                      className={`w-full text-left p-2 rounded transition text-sm ${
                        selectedStudent?.user_id === student.user_id
                          ? 'bg-blue-100 border-blue-500'
                          : 'hover:bg-gray-100'
                      }`}
                    >
                      <div className="font-medium">{student.full_name}</div>
                      <div className="text-xs text-gray-500">Grade {student.grade_level} - {student.section}</div>
                    </button>
                  ))}
                </div>
              </div>

              <div className="md:col-span-2 bg-white rounded-lg shadow-sm p-3" style={{ backgroundColor: '#ffffff' }}>
                {selectedStudent ? (
                  <div>
                    <h3 className="text-base font-semibold mb-3">{selectedStudent.full_name}</h3>
                    <div className="grid grid-cols-2 gap-3 mb-4">
                      <div>
                        <div className="text-xs text-gray-500">Email</div>
                        <div className="text-sm">{selectedStudent.email}</div>
                      </div>
                      <div>
                        <div className="text-xs text-gray-500">Grade & Section</div>
                        <div className="text-sm">Grade {selectedStudent.grade_level}, Section {selectedStudent.section}</div>
                      </div>
                    </div>

                    <h4 className="font-medium mb-2 text-sm">Skill Gaps</h4>
                    {studentGaps.length > 0 ? (
                      <div className="space-y-2">
                        {studentGaps.map((gap) => (
                          <div key={gap.topic_id} className="border rounded-lg p-2">
                            <div className="flex justify-between items-center mb-1">
                              <span className="font-medium text-sm">{gap.topic_name}</span>
                              <span className={`px-2 py-0.5 rounded text-xs ${getWeaknessColor(gap.weakness_level)}`}>
                                {gap.weakness_level} Need
                              </span>
                            </div>
                            <div className="text-xs text-gray-500">
                              Average Score: {gap.avg_score}%
                            </div>
                          </div>
                        ))}
                      </div>
                    ) : (
                      <div className="text-gray-500 text-center py-6 text-sm">
                        No skill gaps detected for this student
                      </div>
                    )}

                    <div className="mt-4 border-t pt-3">
                      <h4 className="font-medium mb-2 text-sm">Generate Practice Material</h4>
                      <div className="flex flex-wrap gap-2 items-end">
                        <div className="flex-1 min-w-32">
                          <label className="block text-xs text-gray-500 mb-1">Topic</label>
                          <select
                            value={generateTopic}
                            onChange={(e) => { setGenerateTopic(e.target.value); setGenerateStatus(''); }}
                            className="w-full border rounded px-2 py-1.5 text-sm focus:outline-none focus:ring-2"
                            style={{ borderColor: '#d1d5db' }}
                          >
                            <option value="">Select weak topic...</option>
                            {studentGaps.length > 0
                              ? studentGaps.map((g) => (
                                  <option key={g.topic_id} value={g.topic_name}>{g.topic_name}</option>
                                ))
                              : ['Algebra', 'Limits', 'Integration'].map((t) => (
                                  <option key={t} value={t}>{t}</option>
                                ))
                            }
                          </select>
                        </div>
                        <div>
                          <label className="block text-xs text-gray-500 mb-1">Difficulty</label>
                          <select
                            value={generateDifficulty}
                            onChange={(e) => setGenerateDifficulty(e.target.value)}
                            className="border rounded px-2 py-1.5 text-sm focus:outline-none focus:ring-2"
                            style={{ borderColor: '#d1d5db' }}
                          >
                            <option value="easy">Easy</option>
                            <option value="medium">Medium</option>
                            <option value="hard">Hard</option>
                          </select>
                        </div>
                        <button
                          onClick={handleGenerateMaterial}
                          disabled={!generateTopic || isGenerating}
                          className="px-3 py-1.5 text-sm rounded transition text-white disabled:opacity-50 disabled:cursor-not-allowed"
                          style={{ backgroundColor: '#2563eb' }}
                        >
                          {isGenerating ? 'Generating...' : 'Generate'}
                        </button>
                      </div>
                      {generateStatus === 'success' && (
                        <p className="mt-2 text-xs text-green-600">Material created and sent for approval.</p>
                      )}
                      {generateStatus === 'error' && (
                        <p className="mt-2 text-xs text-red-600">Failed to generate material. Please try again.</p>
                      )}
                    </div>
                  </div>
                ) : (
                  <div className="text-gray-500 text-center py-8 text-sm">
                    Select a student to view details
                  </div>
                )}
              </div>
            </div>
          </div>
        )}

        {/* Quizzes Tab */}
        {activeTab === 'quizzes' && (
          <div>
            <div className="flex justify-between items-center mb-3">
              <h2 className="text-xl font-bold">Quizzes</h2>
              <button
                onClick={() => setShowCreateQuiz(true)}
                className="px-3 py-1.5 text-sm rounded-md transition text-white"
                style={{ backgroundColor: '#2563eb' }}
              >
                + Create New Quiz
              </button>
            </div>
            
            <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-3">
              {quizzes.map((quiz) => (
                <div key={quiz.quiz_id} className="bg-white rounded-lg shadow-sm p-3" style={{ backgroundColor: '#ffffff' }}>
                  <h3 className="font-medium mb-1 text-sm">{quiz.title}</h3>
                  <p className="text-gray-600 text-xs mb-1">Topic: {quiz.topic}</p>
                  <p className="text-gray-600 text-xs mb-1">Grade: {quiz.grade_level}</p>
                  <p className="text-gray-600 text-xs mb-2">Marks: {quiz.total_marks}</p>
                  <div className="flex gap-1.5">
                    <button
                      onClick={() => handleViewQuizResults(quiz)}
                      className="flex-1 px-2 py-1 text-xs rounded hover:bg-gray-200"
                      style={{ backgroundColor: '#f3f4f6' }}
                    >
                      View Results
                    </button>
                    <button 
                      onClick={() => handleEditQuiz(quiz)}
                      className="flex-1 px-2 py-1 text-xs rounded text-white" 
                      style={{ backgroundColor: '#2563eb' }}
                    >
                      Edit
                    </button>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Pending Approvals Tab */}
        {activeTab === 'approvals' && (
          <div>
            <h2 className="text-xl font-bold mb-3">Pending Approvals</h2>
            
            {pendingMaterials.length > 0 ? (
              <div className="space-y-3">
                {pendingMaterials.map((material) => (
                  <div key={material.material_id} className="bg-white rounded-lg shadow-sm p-3" style={{ backgroundColor: '#ffffff' }}>
                    <div className="flex justify-between items-start mb-3">
                      <div>
                        <h3 className="font-medium text-sm">{material.title}</h3>
                        <p className="text-xs text-gray-500">Topic: {material.topic_name}</p>
                        <p className="text-xs text-gray-500">Generated: {new Date(material.generated_date).toLocaleDateString()}</p>
                      </div>
                      <div className="flex gap-1.5">
                        <button
                          onClick={() => handleApproveMaterial(material.material_id)}
                          className="px-3 py-1 text-xs rounded-md transition text-white"
                          style={{ backgroundColor: '#10b981' }}
                        >
                          Approve
                        </button>
                        <button
                          onClick={() => setShowRejectConfirm(material.material_id)}
                          className="px-3 py-1 text-xs rounded-md transition text-white"
                          style={{ backgroundColor: '#ef4444' }}
                        >
                          Reject
                        </button>
                      </div>
                    </div>
                    <div className="bg-gray-50 rounded p-2 mb-2" style={{ backgroundColor: '#f9fafb' }}>
                      <div
                        className="text-gray-700 text-sm"
                        dangerouslySetInnerHTML={{ __html: material.content }}
                      />
                    </div>
                    {material.source_citation && (
                      <p className="text-xs text-gray-500 italic">Source: {material.source_citation}</p>
                    )}
                  </div>
                ))}
              </div>
            ) : (
              <div className="bg-white rounded-lg shadow-sm p-6 text-center">
                <div className="text-gray-500">No pending approvals</div>
                <p className="text-gray-400 mt-1 text-sm">All materials have been reviewed</p>
              </div>
            )}
          </div>
        )}
      </div>

      {/* Create Quiz Modal */}
      {showCreateQuiz && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-lg shadow-xl w-full max-w-2xl max-h-[85vh] overflow-y-auto p-4" style={{ backgroundColor: '#ffffff' }}>
            <h2 className="text-lg font-bold mb-3">Create New Quiz</h2>
            <form onSubmit={handleCreateQuiz}>
              <div className="grid grid-cols-2 gap-3 mb-3">
                <div>
                  <label className="block text-gray-700 text-sm font-medium mb-1">Quiz Title</label>
                  <input
                    type="text"
                    value={quizForm.title}
                    onChange={(e) => setQuizForm({ ...quizForm, title: e.target.value })}
                    className="w-full px-2 py-1.5 text-sm border rounded focus:outline-none focus:ring-2"
                    style={{ borderColor: '#d1d5db' }}
                    required
                  />
                </div>
                <div>
                  <label className="block text-gray-700 text-sm font-medium mb-1">Topic</label>
                  <select
                    value={quizForm.topic_id}
                    onChange={(e) => setQuizForm({ ...quizForm, topic_id: e.target.value })}
                    className="w-full px-2 py-1.5 text-sm border rounded focus:outline-none focus:ring-2"
                    style={{ borderColor: '#d1d5db' }}
                    required
                  >
                    <option value="">Select Topic</option>
                    <option value="1">Algebra</option>
                    <option value="2">Limits</option>
                    <option value="3">Integration</option>
                  </select>
                </div>
              </div>
              
              <div className="grid grid-cols-2 gap-3 mb-4">
                <div>
                  <label className="block text-gray-700 text-sm font-medium mb-1">Time Limit (minutes)</label>
                  <input
                    type="number"
                    value={quizForm.time_limit}
                    onChange={(e) => setQuizForm({ ...quizForm, time_limit: e.target.value })}
                    className="w-full px-2 py-1.5 text-sm border rounded focus:outline-none focus:ring-2"
                    style={{ borderColor: '#d1d5db' }}
                  />
                </div>
                <div className="flex items-center">
                  <span className="text-sm text-gray-600">{quizForm.questions.length} questions added</span>
                </div>
              </div>

              {/* Add Question Section */}
              <div className="border rounded-lg p-3 mb-4" style={{ borderColor: '#e5e7eb' }}>
                <h3 className="text-sm font-semibold mb-2">Add Question</h3>
                <div className="mb-2">
                  <input
                    type="text"
                    placeholder="Enter question text..."
                    value={newQuestion.question_text}
                    onChange={(e) => setNewQuestion({ ...newQuestion, question_text: e.target.value })}
                    className="w-full px-2 py-1.5 text-sm border rounded"
                    style={{ borderColor: '#d1d5db' }}
                  />
                </div>
                <div className="grid grid-cols-2 gap-2 mb-2">
                  <div className="flex items-center gap-1">
                    <span className="text-xs text-gray-500 w-4">A:</span>
                    <input
                      type="text"
                      placeholder="Option A"
                      value={newQuestion.option_a}
                      onChange={(e) => setNewQuestion({ ...newQuestion, option_a: e.target.value })}
                      className="flex-1 px-2 py-1 text-xs border rounded"
                    />
                  </div>
                  <div className="flex items-center gap-1">
                    <span className="text-xs text-gray-500 w-4">B:</span>
                    <input
                      type="text"
                      placeholder="Option B"
                      value={newQuestion.option_b}
                      onChange={(e) => setNewQuestion({ ...newQuestion, option_b: e.target.value })}
                      className="flex-1 px-2 py-1 text-xs border rounded"
                    />
                  </div>
                  <div className="flex items-center gap-1">
                    <span className="text-xs text-gray-500 w-4">C:</span>
                    <input
                      type="text"
                      placeholder="Option C"
                      value={newQuestion.option_c}
                      onChange={(e) => setNewQuestion({ ...newQuestion, option_c: e.target.value })}
                      className="flex-1 px-2 py-1 text-xs border rounded"
                    />
                  </div>
                  <div className="flex items-center gap-1">
                    <span className="text-xs text-gray-500 w-4">D:</span>
                    <input
                      type="text"
                      placeholder="Option D"
                      value={newQuestion.option_d}
                      onChange={(e) => setNewQuestion({ ...newQuestion, option_d: e.target.value })}
                      className="flex-1 px-2 py-1 text-xs border rounded"
                    />
                  </div>
                </div>
                <div className="flex items-center gap-2 mb-2">
                  <span className="text-xs text-gray-600">Correct Answer:</span>
                  <select
                    value={newQuestion.correct_answer}
                    onChange={(e) => setNewQuestion({ ...newQuestion, correct_answer: e.target.value })}
                    className="px-2 py-1 text-xs border rounded"
                  >
                    <option value="A">A</option>
                    <option value="B">B</option>
                    <option value="C">C</option>
                    <option value="D">D</option>
                  </select>
                </div>
                <button
                  type="button"
                  onClick={handleAddQuestion}
                  className="px-3 py-1.5 text-xs rounded text-white"
                  style={{ backgroundColor: '#10b981' }}
                >
                  + Add Question
                </button>
              </div>

              {/* Questions List */}
              {quizForm.questions.length > 0 && (
                <div className="mb-4">
                  <h3 className="text-sm font-semibold mb-2">Questions ({quizForm.questions.length})</h3>
                  <div className="space-y-2 max-h-40 overflow-y-auto">
                    {quizForm.questions.map((q, idx) => (
                      <div key={idx} className="flex items-start justify-between p-2 rounded" style={{ backgroundColor: '#f9fafb' }}>
                        <div className="flex-1">
                          <p className="text-xs font-medium">{idx + 1}. {q.question_text.substring(0, 60)}...</p>
                          <p className="text-xs text-gray-500">Answer: {q.correct_answer}</p>
                        </div>
                        <button
                          type="button"
                          onClick={() => handleRemoveQuestion(idx)}
                          className="text-red-500 text-xs hover:text-red-700 ml-2"
                        >
                          ✕
                        </button>
                      </div>
                    ))}
                  </div>
                </div>
              )}
              
              <div className="flex justify-end gap-2">
                <button
                  type="button"
                  onClick={() => { setShowCreateQuiz(false); setQuizForm({ title: '', topic_id: '', total_marks: '', time_limit: '30', questions: [] }); }}
                  className="px-3 py-1.5 text-sm rounded-md hover:bg-gray-200"
                  style={{ backgroundColor: '#e5e7eb' }}
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-3 py-1.5 text-sm rounded-md text-white"
                  style={{ backgroundColor: '#2563eb' }}
                >
                  Create Quiz ({quizForm.questions.length} questions)
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Edit Quiz Modal */}
      {showEditQuiz && editingQuiz && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-lg shadow-xl w-full max-w-2xl max-h-[85vh] overflow-y-auto p-4">
            <h2 className="text-lg font-bold mb-3">Edit Quiz</h2>
            <form onSubmit={(e) => { e.preventDefault(); handleUpdateQuiz(); }}>
              <div className="grid grid-cols-2 gap-3 mb-3">
                <div>
                  <label className="block text-gray-700 text-sm font-medium mb-1">Quiz Title</label>
                  <input
                    type="text"
                    value={quizForm.title}
                    onChange={(e) => setQuizForm({ ...quizForm, title: e.target.value })}
                    className="w-full px-2 py-1.5 text-sm border rounded"
                    required
                  />
                </div>
                <div>
                  <label className="block text-gray-700 text-sm font-medium mb-1">Topic</label>
                  <select
                    value={quizForm.topic_id}
                    onChange={(e) => setQuizForm({ ...quizForm, topic_id: e.target.value })}
                    className="w-full px-2 py-1.5 text-sm border rounded"
                    required
                  >
                    <option value="">Select Topic</option>
                    <option value="1">Algebra</option>
                    <option value="2">Limits</option>
                    <option value="3">Integration</option>
                  </select>
                </div>
              </div>
              
              <div className="grid grid-cols-2 gap-3 mb-4">
                <div>
                  <label className="block text-gray-700 text-sm font-medium mb-1">Time Limit (minutes)</label>
                  <input
                    type="number"
                    value={quizForm.time_limit}
                    onChange={(e) => setQuizForm({ ...quizForm, time_limit: e.target.value })}
                    className="w-full px-2 py-1.5 text-sm border rounded"
                  />
                </div>
                <div className="flex items-center">
                  <span className="text-sm text-gray-600">{quizForm.questions.length} questions</span>
                </div>
              </div>

              <div className="border rounded-lg p-3 mb-4">
                <h3 className="text-sm font-semibold mb-2">Add Question</h3>
                <div className="mb-2">
                  <input
                    type="text"
                    placeholder="Enter question text..."
                    value={newQuestion.question_text}
                    onChange={(e) => setNewQuestion({ ...newQuestion, question_text: e.target.value })}
                    className="w-full px-2 py-1.5 text-sm border rounded"
                  />
                </div>
                <div className="grid grid-cols-2 gap-2 mb-2">
                  <div className="flex items-center gap-1">
                    <span className="text-xs text-gray-500 w-4">A:</span>
                    <input type="text" placeholder="Option A" value={newQuestion.option_a} onChange={(e) => setNewQuestion({ ...newQuestion, option_a: e.target.value })} className="flex-1 px-2 py-1 text-xs border rounded" />
                  </div>
                  <div className="flex items-center gap-1">
                    <span className="text-xs text-gray-500 w-4">B:</span>
                    <input type="text" placeholder="Option B" value={newQuestion.option_b} onChange={(e) => setNewQuestion({ ...newQuestion, option_b: e.target.value })} className="flex-1 px-2 py-1 text-xs border rounded" />
                  </div>
                  <div className="flex items-center gap-1">
                    <span className="text-xs text-gray-500 w-4">C:</span>
                    <input type="text" placeholder="Option C" value={newQuestion.option_c} onChange={(e) => setNewQuestion({ ...newQuestion, option_c: e.target.value })} className="flex-1 px-2 py-1 text-xs border rounded" />
                  </div>
                  <div className="flex items-center gap-1">
                    <span className="text-xs text-gray-500 w-4">D:</span>
                    <input type="text" placeholder="Option D" value={newQuestion.option_d} onChange={(e) => setNewQuestion({ ...newQuestion, option_d: e.target.value })} className="flex-1 px-2 py-1 text-xs border rounded" />
                  </div>
                </div>
                <div className="flex items-center gap-2 mb-2">
                  <span className="text-xs text-gray-600">Correct:</span>
                  <select value={newQuestion.correct_answer} onChange={(e) => setNewQuestion({ ...newQuestion, correct_answer: e.target.value })} className="px-2 py-1 text-xs border rounded">
                    <option value="A">A</option>
                    <option value="B">B</option>
                    <option value="C">C</option>
                    <option value="D">D</option>
                  </select>
                </div>
                <button type="button" onClick={handleAddQuestion} className="px-3 py-1.5 text-xs rounded text-white" style={{ backgroundColor: '#10b981' }}>+ Add Question</button>
              </div>

              {quizForm.questions.length > 0 && (
                <div className="mb-4">
                  <h3 className="text-sm font-semibold mb-2">Questions ({quizForm.questions.length})</h3>
                  <div className="space-y-2 max-h-40 overflow-y-auto">
                    {quizForm.questions.map((q, idx) => (
                      <div key={idx} className="flex items-start justify-between p-2 rounded" style={{ backgroundColor: '#f9fafb' }}>
                        <div className="flex-1">
                          <p className="text-xs font-medium">{idx + 1}. {q.question_text.substring(0, 60)}...</p>
                          <p className="text-xs text-gray-500">Answer: {q.correct_answer}</p>
                        </div>
                        <button type="button" onClick={() => handleRemoveQuestion(idx)} className="text-red-500 text-xs hover:text-red-700 ml-2">✕</button>
                      </div>
                    ))}
                  </div>
                </div>
              )}
              
              <div className="flex justify-between">
                <button type="button" onClick={() => { setShowEditQuiz(false); setEditingQuiz(null); setQuizForm({ title: '', topic_id: '', total_marks: '', time_limit: '30', questions: [] }); }} className="px-3 py-1.5 text-sm rounded-md hover:bg-gray-200" style={{ backgroundColor: '#e5e7eb' }}>Cancel</button>
                <button type="submit" className="px-3 py-1.5 text-sm rounded-md text-white" style={{ backgroundColor: '#2563eb' }}>Save Changes</button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* View Results Modal */}
      {showResultsModal && selectedQuizResults && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg shadow-xl w-full max-w-2xl max-h-[80vh] overflow-y-auto p-4" style={{ backgroundColor: '#ffffff' }}>
            <div className="flex justify-between items-center mb-3">
              <h2 className="text-lg font-bold">{selectedQuizResults.quiz.title} - Results</h2>
              <button
                onClick={() => setShowResultsModal(false)}
                className="text-gray-500 hover:text-gray-700 text-lg"
              >
                ✕
              </button>
            </div>
            
            {selectedQuizResults.results.length > 0 ? (
              <table className="w-full text-sm">
                <thead className="bg-gray-100">
                  <tr>
                    <th className="text-left p-2">Student</th>
                    <th className="text-left p-2">Score</th>
                    <th className="text-left p-2">Percentage</th>
                    <th className="text-left p-2">Completed</th>
                  </tr>
                </thead>
                <tbody>
                  {selectedQuizResults.results.map((result, idx) => (
                    <tr key={idx} className="border-b even:bg-gray-50">
                      <td className="p-2">{result.student_name}</td>
                      <td className="p-2">{result.score} / {result.total_marks}</td>
                      <td className="p-2">
                        <span className={`px-2 py-0.5 rounded text-xs ${
                          (result.score / result.total_marks) * 100 >= 70 
                            ? 'bg-green-100 text-green-800' 
                            : 'bg-red-100 text-red-800'
                        }`}>
                          {Math.round((result.score / result.total_marks) * 100)}%
                        </span>
                      </td>
                      <td className="p-2 text-xs text-gray-500">
                        {new Date(result.completed_at).toLocaleDateString()}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            ) : (
              <div className="text-center text-gray-500 py-6">
                No submissions yet for this quiz
              </div>
            )}
          </div>
        </div>
      )}

      {/* Reject Confirmation Modal */}
      {showRejectConfirm && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg shadow-xl w-full max-w-md p-4" style={{ backgroundColor: '#ffffff' }}>
            <h2 className="text-lg font-bold mb-3">Confirm Rejection</h2>
            <p className="text-gray-600 mb-4 text-sm">
              Are you sure you want to reject this material? This action cannot be undone.
            </p>
            <div className="flex justify-end gap-2">
              <button
                onClick={() => setShowRejectConfirm(null)}
                className="px-3 py-1.5 text-sm rounded-md hover:bg-gray-200"
                style={{ backgroundColor: '#e5e7eb' }}
              >
                Cancel
              </button>
              <button
                onClick={() => handleRejectMaterial(showRejectConfirm)}
                className="px-3 py-1.5 text-sm rounded-md text-white"
                style={{ backgroundColor: '#ef4444' }}
              >
                Reject
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Struggling Students Modal */}
      {selectedHeatmapTopic && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg shadow-xl w-full max-w-lg max-h-[80vh] overflow-hidden flex flex-col" style={{ backgroundColor: '#ffffff' }}>
            <div
              className="p-4"
              style={{
                borderTopWidth: '4px',
                borderTopColor: selectedHeatmapTopic.status === 'good' ? '#10b981' : selectedHeatmapTopic.status === 'needs_attention' ? '#f59e0b' : '#ef4444'
              }}
            >
              <div className="flex justify-between items-start">
                <div>
                  <h2 className="text-lg font-bold">{selectedHeatmapTopic.topic_name}</h2>
                  <p className="text-xs text-gray-500">Grade {selectedHeatmapTopic.grade_level}</p>
                </div>
                <button
                  onClick={() => setSelectedHeatmapTopic(null)}
                  className="text-gray-400 hover:text-gray-600 text-2xl leading-none"
                >
                  &times;
                </button>
              </div>
              <div className="grid grid-cols-3 gap-3 mt-3">
                <div className="text-center">
                  <div className="text-xl font-bold text-green-600">{selectedHeatmapTopic.mastered_count}</div>
                  <div className="text-xs text-gray-500">Mastered</div>
                </div>
                <div className="text-center">
                  <div className="text-xl font-bold text-yellow-600">{selectedHeatmapTopic.struggling_count}</div>
                  <div className="text-xs text-gray-500">Struggling</div>
                </div>
                <div className="text-center">
                  <div className="text-xl font-bold text-gray-400">{selectedHeatmapTopic.untouched_count}</div>
                  <div className="text-xs text-gray-500">Not Started</div>
                </div>
              </div>
            </div>
            <div className="p-4 overflow-y-auto flex-1">
              <h3 className="font-medium mb-2 text-red-700 text-sm">Struggling Students</h3>
              {selectedHeatmapTopic.struggling_students && selectedHeatmapTopic.struggling_students.length > 0 ? (
                <div className="space-y-2">
                  {selectedHeatmapTopic.struggling_students.map((student) => (
                    <div key={student.student_id} className="flex justify-between items-center border rounded-lg p-2">
                      <div>
                        <div className="font-medium text-sm">{student.full_name}</div>
                        <div className="text-xs text-gray-500">Average: {student.avg_score}%</div>
                      </div>
                      <div className="flex items-center gap-2">
                        <span className={`px-1.5 py-0.5 rounded text-xs font-medium ${
                          student.avg_score < 40 ? 'bg-red-100 text-red-800' : 'bg-yellow-100 text-yellow-800'
                        }`}>
                          {student.avg_score < 40 ? 'Critical' : 'Needs Work'}
                        </span>
                        <button
                          onClick={() => {
                            setSelectedHeatmapTopic(null);
                            setActiveTab('students');
                            const found = students.find(s => s.user_id === student.student_id);
                            if (found) handleStudentSelect(found);
                          }}
                          className="text-blue-600 hover:text-blue-800 text-xs font-medium"
                        >
                          View
                        </button>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="text-center py-6 text-gray-500 text-sm">
                  No struggling students for this topic
                </div>
              )}
            </div>
            <div className="p-3 border-t bg-gray-50 flex justify-end">
              <button
                onClick={() => setSelectedHeatmapTopic(null)}
                className="px-3 py-1.5 text-sm rounded-md hover:bg-gray-200"
                style={{ backgroundColor: '#e5e7eb' }}
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default TeacherDashboard;