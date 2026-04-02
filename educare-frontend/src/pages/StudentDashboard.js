import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { getQuizzes, getApprovedMaterials, getProgressMap, getAvailableTopics, getStudentRecommendations, getCompletedQuizzes } from '../services/api';

function StudentDashboard() {
  const [quizzes, setQuizzes] = useState([]);
  const [materials, setMaterials] = useState([]);
  const [progressMap, setProgressMap] = useState({});
  const [grades, setGrades] = useState([]);
  const [availableTopics, setAvailableTopics] = useState([]);
  const [recommendations, setRecommendations] = useState([]);
  const [completedQuizzes, setCompletedQuizzes] = useState({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [activeTab, setActiveTab] = useState('progress');
  const navigate = useNavigate();
  const fullName = localStorage.getItem('full_name');
  const userId = localStorage.getItem('user_id');

  useEffect(() => {
    const fetchData = async () => {
      try {
        const [quizzesData, materialsData, progressData, topicsData, recsData, completedData] = await Promise.all([
          getQuizzes(),
          getApprovedMaterials(userId),
          getProgressMap(userId),
          getAvailableTopics(userId),
          getStudentRecommendations(userId),
          getCompletedQuizzes(userId)
        ]);
        setQuizzes(quizzesData.quizzes || []);
        setMaterials(materialsData.materials || []);
        setProgressMap(progressData.progress_map || {});
        setGrades(progressData.grades || []);
        setAvailableTopics(topicsData.topics || []);
        setRecommendations(recsData.recommendations || []);
        setCompletedQuizzes(completedData.completed_quizzes || {});
      } catch (err) {
        setError('Failed to load data');
      } finally {
        setLoading(false);
      }
    };
    fetchData();
  }, [userId]);

  const handleLogout = () => {
    localStorage.clear();
    navigate('/login');
  };

  const getColorClasses = (color) => {
    switch (color) {
      case 'green':
        return 'bg-green-50 border-green-400 text-green-800';
      case 'yellow':
        return 'bg-yellow-50 border-yellow-400 text-yellow-800';
      case 'blue':
        return 'bg-blue-50 border-blue-400 text-blue-800';
      case 'gray':
      default:
        return 'bg-gray-50 border-gray-300 text-gray-500';
    }
  };

  const getStatusLabel = (color) => {
    switch (color) {
      case 'green': return 'Mastered';
      case 'yellow': return 'In Progress';
      case 'blue': return 'Available';
      case 'gray': return 'Locked';
      default: return 'Unknown';
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-[#f3f4f6]">
        <div className="flex items-center gap-3">
          <div className="w-6 h-6 border-2 border-[#2563eb] border-t-transparent rounded-full animate-spin"></div>
          <span className="text-gray-500 text-sm">Loading dashboard...</span>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-[#f3f4f6]">
      {/* Navbar */}
      <nav className="bg-white border-b border-gray-200 sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-4 h-14 flex justify-between items-center">
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 bg-[#2563eb] rounded-lg flex items-center justify-center">
              <svg className="w-4 h-4 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" />
              </svg>
            </div>
            <span className="text-base font-bold text-gray-900">EDUCARE</span>
          </div>
          <div className="flex items-center gap-3">
            <span className="text-sm text-gray-600 hidden sm:block">{fullName}</span>
            <button
              onClick={handleLogout}
              className="text-sm text-gray-500 hover:text-red-600 px-3 py-1.5 rounded-md hover:bg-red-50 transition font-medium"
            >
              Logout
            </button>
          </div>
        </div>
      </nav>

      {/* Tabs */}
      <div className="bg-white border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4">
          <div className="flex gap-1">
            {[
              { key: 'progress', label: 'Progress Map' },
              { key: 'quizzes', label: 'Quizzes' },
              { key: 'materials', label: 'Materials' },
            ].map((tab) => (
              <button
                key={tab.key}
                onClick={() => setActiveTab(tab.key)}
                className={`py-2.5 px-4 text-sm font-medium transition border-b-2 ${
                  activeTab === tab.key
                    ? 'text-[#2563eb] border-[#2563eb]'
                    : 'text-gray-500 border-transparent hover:text-gray-700 hover:border-gray-300'
                }`}
              >
                {tab.label}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="max-w-7xl mx-auto px-4 py-4">
        {error && (
          <div className="bg-red-50 border border-red-200 text-red-700 px-3 py-2 rounded-lg mb-4 text-sm">
            {error}
          </div>
        )}

        {/* Progress Map Tab */}
        {activeTab === 'progress' && (
          <div>
            <div className="mb-4">
              <h2 className="text-xl font-bold text-gray-900 mb-1">Topic Progression Map</h2>
              <p className="text-sm text-gray-500">Track your mastery across all topics. Complete prerequisites to unlock new ones.</p>
            </div>

            {/* Legend */}
            <div className="flex gap-4 mb-4 flex-wrap">
              {[
                { color: 'bg-green-500', label: 'Mastered (70%+)' },
                { color: 'bg-yellow-500', label: 'In Progress' },
                { color: 'bg-blue-500', label: 'Available' },
                { color: 'bg-gray-400', label: 'Locked' },
              ].map((item) => (
                <div key={item.label} className="flex items-center gap-1.5">
                  <div className={`w-3 h-3 rounded ${item.color}`}></div>
                  <span className="text-xs text-gray-500">{item.label}</span>
                </div>
              ))}
            </div>

            {/* Progress by Grade */}
            {grades.map((grade) => (
              <div key={grade} className="mb-6">
                <h3 className="text-sm font-semibold mb-2 text-gray-600 uppercase tracking-wide">Grade {grade}</h3>
                <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5 gap-3">
                  {(progressMap[grade] || []).map((topic) => (
                    <div
                      key={topic.topic_id}
                      className={`w-full rounded-lg border p-3 transition ${getColorClasses(topic.color)} ${
                        topic.color === 'blue' ? 'cursor-pointer hover:shadow-md' : ''
                      }`}
                      onClick={() => {
                        if (topic.color === 'blue') {
                          const quiz = quizzes.find(q => q.topic === topic.topic_name);
                          if (quiz) navigate(`/quiz/${quiz.quiz_id}`);
                        }
                      }}
                      title={
                        topic.color === 'gray' && topic.prerequisite_names.length > 0
                          ? `Complete ${topic.prerequisite_names.join(', ')} first`
                          : ''
                      }
                    >
                      <div className="flex justify-between items-start mb-1.5">
                        <h4 className="font-semibold text-xs leading-tight">{topic.topic_name}</h4>
                        <span className={`text-[10px] px-1.5 py-0.5 rounded-full flex-shrink-0 ml-1 ${
                          topic.color === 'green' ? 'bg-green-200' :
                          topic.color === 'yellow' ? 'bg-yellow-200' :
                          topic.color === 'blue' ? 'bg-blue-200' : 'bg-gray-200'
                        }`}>
                          {getStatusLabel(topic.color)}
                        </span>
                      </div>
                      {topic.avg_score !== null && (
                        <div>
                          <div className="text-[10px] text-gray-600 mb-1">{topic.avg_score}%</div>
                          <div className="w-full bg-white bg-opacity-60 rounded-full h-1.5">
                            <div
                              className={`h-1.5 rounded-full ${
                                topic.avg_score >= 70 ? 'bg-green-500' : 'bg-yellow-500'
                              }`}
                              style={{ width: `${Math.min(topic.avg_score, 100)}%` }}
                            ></div>
                          </div>
                        </div>
                      )}
                      {topic.color === 'gray' && topic.prerequisite_names.length > 0 && (
                        <p className="text-[10px] mt-1 opacity-75 leading-tight">
                          Need: {topic.prerequisite_names.join(', ')}
                        </p>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            ))}

            {grades.length === 0 && (
              <div className="bg-white rounded-lg shadow-sm p-8 text-center">
                <p className="text-gray-400 text-sm">No topics available yet</p>
              </div>
            )}
          </div>
        )}

        {/* Quizzes Tab */}
        {activeTab === 'quizzes' && (
          <div>
            {/* Recommended */}
            <div className="mb-6">
              <h2 className="text-xl font-bold text-gray-900 mb-1">Recommended for You</h2>
              <p className="text-sm text-gray-500 mb-3">Quizzes picked based on your performance.</p>
              {recommendations.length > 0 ? (
                <div className="flex gap-3 overflow-x-auto pb-2 -mx-1 px-1">
                  {recommendations.map((rec) => {
                    const bestScore = completedQuizzes[String(rec.quiz_id)];
                    const completed = bestScore !== undefined;
                    return (
                    <div
                      key={rec.quiz_id}
                      className={`flex-shrink-0 w-64 rounded-lg shadow-sm p-3 hover:shadow-md transition ${
                        completed ? 'bg-green-50 border border-green-200' : 'bg-white border border-blue-100'
                      }`}
                    >
                      <div className="flex items-center gap-1.5 mb-1.5">
                        <span className="text-[10px] px-1.5 py-0.5 rounded-full bg-blue-100 text-blue-700 font-medium">
                          {rec.topic_name}
                        </span>
                        {completed ? (
                          <span className="text-[10px] px-1.5 py-0.5 rounded-full bg-green-100 text-green-700 font-medium">
                            ✓ {bestScore}%
                          </span>
                        ) : rec.avg_score !== null && (
                          <span className={`text-[10px] px-1.5 py-0.5 rounded-full font-medium ${
                            rec.avg_score < 40 ? 'bg-red-100 text-red-700' : 'bg-yellow-100 text-yellow-700'
                          }`}>
                            {rec.avg_score}%
                          </span>
                        )}
                      </div>
                      <h3 className="font-semibold text-gray-800 text-sm mb-1">{rec.title}</h3>
                      <p className="text-xs text-gray-500 mb-2 line-clamp-2">{rec.reason}</p>
                      <div className="flex items-center justify-between">
                        <span className="text-[10px] text-gray-400">{rec.total_marks} marks</span>
                        <button
                          onClick={() => navigate(`/quiz/${rec.quiz_id}`)}
                          className={`px-3 py-1 rounded-md text-xs font-medium transition ${
                            completed
                              ? 'bg-white border border-green-300 text-green-700 hover:bg-green-100'
                              : 'bg-[#2563eb] text-white hover:bg-[#1d4ed8]'
                          }`}
                        >
                          {completed ? 'Retake' : 'Take Quiz'}
                        </button>
                      </div>
                    </div>
                    );
                  })}
                </div>
              ) : (
                <div className="bg-white rounded-lg shadow-sm p-6 text-center">
                  <p className="text-sm font-medium text-gray-600">No recommendations right now</p>
                  <p className="text-xs text-gray-400 mt-0.5">You're performing well across all topics.</p>
                </div>
              )}
            </div>

            <h2 className="text-xl font-bold text-gray-900 mb-3">Available Quizzes</h2>

            {availableTopics.filter(t => t.prerequisites_met).length > 0 ? (
              <div className="space-y-3">
                {availableTopics.filter(t => t.prerequisites_met).map((topic) => {
                  const topicQuizzes = quizzes.filter(q => q.topic === topic.topic_name);
                  if (topicQuizzes.length === 0) return null;
                  return (
                    <div key={topic.topic_id} className="bg-white rounded-lg shadow-sm p-4">
                      <div className="flex justify-between items-center mb-3">
                        <h3 className="text-sm font-semibold text-gray-900">{topic.topic_name}</h3>
                        <span className={`text-[10px] px-2 py-0.5 rounded-full font-medium ${
                          topic.status === 'mastered' ? 'bg-green-100 text-green-700' :
                          topic.status === 'in_progress' ? 'bg-yellow-100 text-yellow-700' :
                          'bg-blue-100 text-blue-700'
                        }`}>
                          {topic.status === 'mastered' ? 'Mastered' :
                           topic.status === 'in_progress' ? `In Progress (${topic.avg_score}%)` : 'Not Started'}
                        </span>
                      </div>
                      <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-3">
                        {topicQuizzes.map((quiz) => {
                          const bestScore = completedQuizzes[String(quiz.quiz_id)];
                          const completed = bestScore !== undefined;
                          return (
                            <div key={quiz.quiz_id} className={`border rounded-lg p-3 transition ${completed ? 'border-green-200 bg-green-50' : 'border-gray-200 hover:border-gray-300'}`}>
                              <div className="flex items-center justify-between mb-1">
                                <h4 className="font-medium text-sm text-gray-900">{quiz.title}</h4>
                                {completed && (
                                  <span className="text-[10px] px-1.5 py-0.5 rounded-full bg-green-100 text-green-700 font-medium flex-shrink-0 ml-1">
                                    ✓ Done
                                  </span>
                                )}
                              </div>
                              <p className="text-xs text-gray-500 mb-1">{quiz.total_marks} marks</p>
                              {completed && (
                                <p className="text-xs text-green-700 font-medium mb-2">Best: {bestScore}/{quiz.total_marks}</p>
                              )}
                              <button
                                onClick={() => navigate(`/quiz/${quiz.quiz_id}`)}
                                className={`w-full py-1.5 rounded-md text-xs font-medium transition ${
                                  completed
                                    ? 'bg-white border border-green-300 text-green-700 hover:bg-green-100'
                                    : 'bg-[#2563eb] text-white hover:bg-[#1d4ed8]'
                                }`}
                              >
                                {completed ? 'Retake' : 'Take Quiz'}
                              </button>
                            </div>
                          );
                        })}
                      </div>
                    </div>
                  );
                })}
              </div>
            ) : (
              <div className="bg-white rounded-lg shadow-sm p-8 text-center">
                <p className="text-gray-400 text-sm">No quizzes available</p>
              </div>
            )}

            {/* Locked topics */}
            {availableTopics.filter(t => !t.prerequisites_met).length > 0 && (
              <div className="mt-6">
                <h3 className="text-sm font-semibold mb-2 text-gray-500 uppercase tracking-wide">Locked Topics</h3>
                <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-3">
                  {availableTopics.filter(t => !t.prerequisites_met).map((topic) => (
                    <div key={topic.topic_id} className="bg-gray-50 rounded-lg p-3 opacity-60">
                      <h4 className="font-medium text-sm text-gray-500">{topic.topic_name}</h4>
                      <p className="text-xs text-gray-400 mt-0.5">Complete prerequisites first</p>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}

        {/* Materials Tab */}
        {activeTab === 'materials' && (
          <div>
            <h2 className="text-xl font-bold text-gray-900 mb-3">Study Materials</h2>
            {materials.length > 0 ? (
              <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-4">
                {materials.map((material) => (
                  <div key={material.material_id} className="bg-white rounded-lg shadow-sm p-4">
                    <h3 className="text-sm font-semibold text-gray-900 mb-1">{material.title}</h3>
                    <div className="flex items-center gap-2 mb-2">
                      <span className="text-[10px] px-1.5 py-0.5 rounded-full bg-blue-100 text-blue-700 font-medium">
                        {material.topic_name}
                      </span>
                      <span className="text-[10px] text-gray-400">
                        {new Date(material.generated_date).toLocaleDateString()}
                      </span>
                    </div>
                    <div className="bg-gray-50 rounded-md p-3 mb-2 max-h-40 overflow-y-auto">
                      <p className="text-xs text-gray-700 whitespace-pre-wrap leading-relaxed">{material.content}</p>
                    </div>
                    {material.source_citation && (
                      <p className="text-[10px] text-gray-400 italic">Source: {material.source_citation}</p>
                    )}
                  </div>
                ))}
              </div>
            ) : (
              <div className="bg-white rounded-lg shadow-sm p-8 text-center">
                <p className="text-gray-400 text-sm">No study materials available</p>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}

export default StudentDashboard;
