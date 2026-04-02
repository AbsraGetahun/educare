import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { getQuizzes, getStudents, getStudentGaps, getQuizResults, createQuiz, getPendingMaterials, approveMaterial, rejectMaterial, getTeacherMasteryOverview, getHeatmap } from '../services/api';

function TeacherDashboard() {
  const [activeTab, setActiveTab] = useState('overview');
  const [quizzes, setQuizzes] = useState([]);
  const [students, setStudents] = useState([]);
  const [selectedStudent, setSelectedStudent] = useState(null);
  const [studentGaps, setStudentGaps] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [showCreateQuiz, setShowCreateQuiz] = useState(false);
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
    time_limit: '30'
  });
  const navigate = useNavigate();
  const fullName = localStorage.getItem('full_name');

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    setLoading(true);
    try {
      const [quizzesData, studentsData, materialsData, masteryData] = await Promise.all([
        getQuizzes(),
        getStudents(),
        getPendingMaterials(),
        getTeacherMasteryOverview()
      ]);
      setQuizzes(quizzesData.quizzes || []);
      setStudents(studentsData.students || []);
      setPendingMaterials(materialsData.materials || []);
      setMasteryOverview(masteryData.overview || []);
      setTotalStudents(masteryData.total_students || 0);
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
    if (!quizForm.title || !quizForm.topic_id || !quizForm.total_marks) {
      alert('Please fill all required fields');
      return;
    }

    try {
      await createQuiz(quizForm);
      alert('Quiz created successfully!');
      setShowCreateQuiz(false);
      setQuizForm({ title: '', topic_id: '', total_marks: '', time_limit: '30' });
      fetchData();
    } catch (err) {
      alert('Failed to create quiz');
    }
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
    <div className="min-h-screen bg-gray-100">
      {/* Navigation Bar */}
      <nav className="bg-white shadow-md p-4 sticky top-0 z-10">
        <div className="container mx-auto flex justify-between items-center">
          <div className="flex items-center gap-4">
            <h1 className="text-xl font-bold text-blue-600">EDUCARE</h1>
            <span className="text-gray-400">|</span>
            <span className="text-gray-600">Teacher Portal</span>
          </div>
          <div className="flex items-center gap-4">
            <span className="text-gray-600">Welcome, {fullName}</span>
            <button
              onClick={handleLogout}
              className="bg-red-500 text-white px-4 py-2 rounded hover:bg-red-600 transition"
            >
              Logout
            </button>
          </div>
        </div>
      </nav>

      {/* Tabs */}
      <div className="bg-white border-b">
        <div className="container mx-auto">
          <div className="flex space-x-8">
            <button
              onClick={() => setActiveTab('overview')}
              className={`py-4 px-2 font-medium transition ${
                activeTab === 'overview'
                  ? 'text-blue-600 border-b-2 border-blue-600'
                  : 'text-gray-500 hover:text-gray-700'
              }`}
            >
              Class Overview
            </button>
            <button
              onClick={() => setActiveTab('mastery')}
              className={`py-4 px-2 font-medium transition ${
                activeTab === 'mastery'
                  ? 'text-blue-600 border-b-2 border-blue-600'
                  : 'text-gray-500 hover:text-gray-700'
              }`}
            >
              Mastery Tracker
            </button>
            <button
              onClick={() => setActiveTab('students')}
              className={`py-4 px-2 font-medium transition ${
                activeTab === 'students'
                  ? 'text-blue-600 border-b-2 border-blue-600'
                  : 'text-gray-500 hover:text-gray-700'
              }`}
            >
              Students
            </button>
            <button
              onClick={() => setActiveTab('quizzes')}
              className={`py-4 px-2 font-medium transition ${
                activeTab === 'quizzes'
                  ? 'text-blue-600 border-b-2 border-blue-600'
                  : 'text-gray-500 hover:text-gray-700'
              }`}
            >
              Quizzes
            </button>
            <button
              onClick={() => setActiveTab('approvals')}
              className={`py-4 px-2 font-medium transition ${
                activeTab === 'approvals'
                  ? 'text-blue-600 border-b-2 border-blue-600'
                  : 'text-gray-500 hover:text-gray-700'
              }`}
            >
              Pending Approvals ({pendingMaterials.length})
            </button>
          </div>
        </div>
      </div>

      {/* Content */}
      <div className="container mx-auto p-6">
        {error && (
          <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded mb-4">
            {error}
          </div>
        )}

        {/* Overview Tab */}
        {activeTab === 'overview' && (
          <div>
            <h2 className="text-2xl font-bold mb-6">Class Overview</h2>
            
            <div className="grid md:grid-cols-3 gap-6 mb-8">
              <div className="bg-white rounded-lg shadow-md p-6">
                <div className="text-3xl font-bold text-blue-600">{students.length}</div>
                <div className="text-gray-600">Total Students</div>
              </div>
              <div className="bg-white rounded-lg shadow-md p-6">
                <div className="text-3xl font-bold text-green-600">{quizzes.length}</div>
                <div className="text-gray-600">Active Quizzes</div>
              </div>
              <div className="bg-white rounded-lg shadow-md p-6">
                <div className="text-3xl font-bold text-yellow-600">{pendingMaterials.length}</div>
                <div className="text-gray-600">Pending Approvals</div>
              </div>
            </div>

            {/* Quick Mastery Summary */}
            <div className="bg-white rounded-lg shadow-md p-6 mb-8">
              <h3 className="text-lg font-semibold mb-4">Topic Mastery Summary</h3>
              <div className="overflow-x-auto">
                <table className="w-full">
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
                      <tr key={topic.topic_id} className="border-b">
                        <td className="py-2">{topic.topic_name}</td>
                        <td className="py-2">{topic.grade_level}</td>
                        <td className="py-2">
                          <div className="flex items-center gap-2">
                            <div className="w-24 bg-gray-200 rounded-full h-2">
                              <div
                                className={`h-2 rounded-full ${getMasteryBarColor(topic.mastery_pct)}`}
                                style={{ width: `${topic.mastery_pct}%` }}
                              ></div>
                            </div>
                            <span className="text-sm">{topic.mastery_pct}%</span>
                          </div>
                        </td>
                        <td className="py-2">{topic.mastered_count}/{topic.total_students}</td>
                        <td className="py-2">
                          <span className={`px-2 py-1 rounded text-sm ${
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
            <h2 className="text-2xl font-bold mb-6">Mastery Tracker</h2>
            <p className="text-gray-600 mb-6">Click on a topic to view students who need remediation or are blocked by prerequisites.</p>

            <div className="space-y-4">
              {masteryOverview.map((topic) => (
                <div key={topic.topic_id} className="bg-white rounded-lg shadow-md overflow-hidden">
                  <button
                    onClick={() => setExpandedTopic(expandedTopic === topic.topic_id ? null : topic.topic_id)}
                    className="w-full p-4 flex justify-between items-center hover:bg-gray-50 transition"
                  >
                    <div className="flex items-center gap-4">
                      <div className={`w-12 h-12 rounded-lg flex items-center justify-center text-white font-bold ${
                        topic.mastery_pct >= 70 ? 'bg-green-500' :
                        topic.mastery_pct >= 40 ? 'bg-yellow-500' : 'bg-red-500'
                      }`}>
                        {topic.mastery_pct}%
                      </div>
                      <div className="text-left">
                        <h3 className="font-semibold">{topic.topic_name}</h3>
                        <p className="text-sm text-gray-500">Grade {topic.grade_level} - {topic.mastered_count} of {topic.total_students} students mastered</p>
                      </div>
                    </div>
                    <div className="flex items-center gap-4">
                      {topic.struggling_students.length > 0 && (
                        <span className="bg-red-100 text-red-800 px-2 py-1 rounded text-sm">
                          {topic.struggling_students.length} struggling
                        </span>
                      )}
                      {topic.blocked_students.length > 0 && (
                        <span className="bg-gray-100 text-gray-800 px-2 py-1 rounded text-sm">
                          {topic.blocked_students.length} blocked
                        </span>
                      )}
                      <span className="text-gray-400">{expandedTopic === topic.topic_id ? '▲' : '▼'}</span>
                    </div>
                  </button>

                  {expandedTopic === topic.topic_id && (
                    <div className="border-t p-4 bg-gray-50">
                      {/* Mastery Progress Bar */}
                      <div className="mb-4">
                        <div className="flex justify-between text-sm mb-1">
                          <span>Class Mastery</span>
                          <span>{topic.mastered_count}/{topic.total_students} students ({topic.mastery_pct}%)</span>
                        </div>
                        <div className="w-full bg-gray-200 rounded-full h-3">
                          <div
                            className={`h-3 rounded-full ${getMasteryBarColor(topic.mastery_pct)}`}
                            style={{ width: `${topic.mastery_pct}%` }}
                          ></div>
                        </div>
                      </div>

                      <div className="grid md:grid-cols-2 gap-4">
                        {/* Struggling Students */}
                        <div>
                          <h4 className="font-semibold mb-2 text-red-700">Needs Remediation</h4>
                          {topic.struggling_students.length > 0 ? (
                            <div className="space-y-2">
                              {topic.struggling_students.map((student) => (
                                <div key={student.student_id} className="flex justify-between items-center bg-white rounded p-2 border">
                                  <span className="text-sm">{student.full_name}</span>
                                  <span className="text-sm text-red-600 font-medium">{student.avg_score}%</span>
                                </div>
                              ))}
                            </div>
                          ) : (
                            <p className="text-sm text-gray-500 bg-white rounded p-2 border">No struggling students</p>
                          )}
                        </div>

                        {/* Blocked Students */}
                        <div>
                          <h4 className="font-semibold mb-2 text-gray-700">Blocked by Prerequisites</h4>
                          {topic.blocked_students.length > 0 ? (
                            <div className="space-y-2">
                              {topic.blocked_students.map((student) => (
                                <div key={student.student_id} className="flex justify-between items-center bg-white rounded p-2 border">
                                  <span className="text-sm">{student.full_name}</span>
                                  <span className="text-sm text-gray-500">Not started</span>
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
                <div className="bg-white rounded-lg shadow-md p-12 text-center">
                  <p className="text-gray-500 text-lg">No mastery data available</p>
                </div>
              )}
            </div>
          </div>
        )}

        {/* Students Tab */}
        {activeTab === 'students' && (
          <div>
            <h2 className="text-2xl font-bold mb-6">Student Management</h2>
            
            <div className="grid md:grid-cols-3 gap-6">
              <div className="bg-white rounded-lg shadow-md p-4">
                <h3 className="font-semibold mb-3">Students</h3>
                <div className="space-y-2 max-h-96 overflow-y-auto">
                  {students.map((student) => (
                    <button
                      key={student.user_id}
                      onClick={() => handleStudentSelect(student)}
                      className={`w-full text-left p-3 rounded transition ${
                        selectedStudent?.user_id === student.user_id
                          ? 'bg-blue-100 border-blue-500'
                          : 'hover:bg-gray-100'
                      }`}
                    >
                      <div className="font-medium">{student.full_name}</div>
                      <div className="text-sm text-gray-500">Grade {student.grade_level} - {student.section}</div>
                    </button>
                  ))}
                </div>
              </div>

              <div className="md:col-span-2 bg-white rounded-lg shadow-md p-6">
                {selectedStudent ? (
                  <div>
                    <h3 className="text-xl font-semibold mb-4">{selectedStudent.full_name}</h3>
                    <div className="grid grid-cols-2 gap-4 mb-6">
                      <div>
                        <div className="text-sm text-gray-500">Email</div>
                        <div>{selectedStudent.email}</div>
                      </div>
                      <div>
                        <div className="text-sm text-gray-500">Grade & Section</div>
                        <div>Grade {selectedStudent.grade_level}, Section {selectedStudent.section}</div>
                      </div>
                    </div>

                    <h4 className="font-semibold mb-3">Skill Gaps</h4>
                    {studentGaps.length > 0 ? (
                      <div className="space-y-3">
                        {studentGaps.map((gap) => (
                          <div key={gap.topic_id} className="border rounded-lg p-3">
                            <div className="flex justify-between items-center mb-2">
                              <span className="font-medium">{gap.topic_name}</span>
                              <span className={`px-2 py-1 rounded text-sm ${getWeaknessColor(gap.weakness_level)}`}>
                                {gap.weakness_level} Need
                              </span>
                            </div>
                            <div className="text-sm text-gray-500">
                              Average Score: {gap.avg_score}%
                            </div>
                          </div>
                        ))}
                      </div>
                    ) : (
                      <div className="text-gray-500 text-center py-8">
                        No skill gaps detected for this student
                      </div>
                    )}
                  </div>
                ) : (
                  <div className="text-gray-500 text-center py-12">
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
            <div className="flex justify-between items-center mb-6">
              <h2 className="text-2xl font-bold">Quizzes</h2>
              <button
                onClick={() => setShowCreateQuiz(true)}
                className="bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700"
              >
                + Create New Quiz
              </button>
            </div>
            
            <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
              {quizzes.map((quiz) => (
                <div key={quiz.quiz_id} className="bg-white rounded-lg shadow-md p-6">
                  <h3 className="text-lg font-semibold mb-2">{quiz.title}</h3>
                  <p className="text-gray-600 text-sm mb-2">Topic: {quiz.topic}</p>
                  <p className="text-gray-600 text-sm mb-2">Grade: {quiz.grade_level}</p>
                  <p className="text-gray-600 text-sm mb-4">Marks: {quiz.total_marks}</p>
                  <div className="flex gap-2">
                    <button
                      onClick={() => handleViewQuizResults(quiz)}
                      className="flex-1 bg-gray-200 text-gray-700 py-2 rounded hover:bg-gray-300"
                    >
                      View Results
                    </button>
                    <button className="flex-1 bg-blue-600 text-white py-2 rounded hover:bg-blue-700">
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
            <h2 className="text-2xl font-bold mb-6">Pending Approvals</h2>
            
            {pendingMaterials.length > 0 ? (
              <div className="space-y-4">
                {pendingMaterials.map((material) => (
                  <div key={material.material_id} className="bg-white rounded-lg shadow-md p-6">
                    <div className="flex justify-between items-start mb-4">
                      <div>
                        <h3 className="text-lg font-semibold">{material.title}</h3>
                        <p className="text-sm text-gray-500">Topic: {material.topic_name}</p>
                        <p className="text-sm text-gray-500">Generated: {new Date(material.generated_date).toLocaleDateString()}</p>
                      </div>
                      <div className="flex gap-2">
                        <button
                          onClick={() => handleApproveMaterial(material.material_id)}
                          className="bg-green-600 text-white px-4 py-2 rounded hover:bg-green-700 transition"
                        >
                          Approve
                        </button>
                        <button
                          onClick={() => setShowRejectConfirm(material.material_id)}
                          className="bg-red-600 text-white px-4 py-2 rounded hover:bg-red-700 transition"
                        >
                          Reject
                        </button>
                      </div>
                    </div>
                    <div className="bg-gray-50 rounded p-4 mb-4">
                      <p className="text-gray-700 whitespace-pre-wrap">{material.content}</p>
                    </div>
                    {material.source_citation && (
                      <p className="text-sm text-gray-500 italic">Source: {material.source_citation}</p>
                    )}
                  </div>
                ))}
              </div>
            ) : (
              <div className="bg-white rounded-lg shadow-md p-12 text-center">
                <div className="text-gray-500 text-lg">No pending approvals</div>
                <p className="text-gray-400 mt-2">All materials have been reviewed</p>
              </div>
            )}
          </div>
        )}
      </div>

      {/* Create Quiz Modal */}
      {showCreateQuiz && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg shadow-xl w-full max-w-md p-6">
            <h2 className="text-xl font-bold mb-4">Create New Quiz</h2>
            <form onSubmit={handleCreateQuiz}>
              <div className="mb-4">
                <label className="block text-gray-700 text-sm font-bold mb-2">Quiz Title</label>
                <input
                  type="text"
                  value={quizForm.title}
                  onChange={(e) => setQuizForm({ ...quizForm, title: e.target.value })}
                  className="w-full px-3 py-2 border rounded focus:outline-none focus:ring-2 focus:ring-blue-500"
                  required
                />
              </div>
              
              <div className="mb-4">
                <label className="block text-gray-700 text-sm font-bold mb-2">Topic ID</label>
                <input
                  type="number"
                  value={quizForm.topic_id}
                  onChange={(e) => setQuizForm({ ...quizForm, topic_id: e.target.value })}
                  className="w-full px-3 py-2 border rounded"
                  placeholder="1 for Algebra, 2 for Limits, 3 for Integration"
                  required
                />
              </div>
              
              <div className="mb-4">
                <label className="block text-gray-700 text-sm font-bold mb-2">Total Marks</label>
                <input
                  type="number"
                  value={quizForm.total_marks}
                  onChange={(e) => setQuizForm({ ...quizForm, total_marks: e.target.value })}
                  className="w-full px-3 py-2 border rounded"
                  required
                />
              </div>
              
              <div className="mb-6">
                <label className="block text-gray-700 text-sm font-bold mb-2">Time Limit (minutes)</label>
                <input
                  type="number"
                  value={quizForm.time_limit}
                  onChange={(e) => setQuizForm({ ...quizForm, time_limit: e.target.value })}
                  className="w-full px-3 py-2 border rounded"
                />
              </div>
              
              <div className="flex justify-end gap-3">
                <button
                  type="button"
                  onClick={() => setShowCreateQuiz(false)}
                  className="px-4 py-2 bg-gray-300 rounded hover:bg-gray-400"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
                >
                  Create Quiz
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* View Results Modal */}
      {showResultsModal && selectedQuizResults && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg shadow-xl w-full max-w-2xl max-h-[80vh] overflow-y-auto p-6">
            <div className="flex justify-between items-center mb-4">
              <h2 className="text-xl font-bold">{selectedQuizResults.quiz.title} - Results</h2>
              <button
                onClick={() => setShowResultsModal(false)}
                className="text-gray-500 hover:text-gray-700 text-xl"
              >
                ✕
              </button>
            </div>
            
            {selectedQuizResults.results.length > 0 ? (
              <table className="w-full">
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
                    <tr key={idx} className="border-b">
                      <td className="p-2">{result.student_name}</td>
                      <td className="p-2">{result.score} / {result.total_marks}</td>
                      <td className="p-2">
                        <span className={`px-2 py-1 rounded text-sm ${
                          (result.score / result.total_marks) * 100 >= 70 
                            ? 'bg-green-100 text-green-800' 
                            : 'bg-red-100 text-red-800'
                        }`}>
                          {Math.round((result.score / result.total_marks) * 100)}%
                        </span>
                      </td>
                      <td className="p-2 text-sm text-gray-500">
                        {new Date(result.completed_at).toLocaleDateString()}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            ) : (
              <div className="text-center text-gray-500 py-8">
                No submissions yet for this quiz
              </div>
            )}
          </div>
        </div>
      )}

      {/* Reject Confirmation Modal */}
      {showRejectConfirm && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg shadow-xl w-full max-w-md p-6">
            <h2 className="text-xl font-bold mb-4">Confirm Rejection</h2>
            <p className="text-gray-600 mb-6">
              Are you sure you want to reject this material? This action cannot be undone.
            </p>
            <div className="flex justify-end gap-3">
              <button
                onClick={() => setShowRejectConfirm(null)}
                className="px-4 py-2 bg-gray-300 rounded hover:bg-gray-400"
              >
                Cancel
              </button>
              <button
                onClick={() => handleRejectMaterial(showRejectConfirm)}
                className="px-4 py-2 bg-red-600 text-white rounded hover:bg-red-700"
              >
                Reject
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default TeacherDashboard;
