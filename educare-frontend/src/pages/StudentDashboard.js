import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { getQuizzes, getApprovedMaterials, getProgressMap, getAvailableTopics } from '../services/api';

function StudentDashboard() {
  const [quizzes, setQuizzes] = useState([]);
  const [materials, setMaterials] = useState([]);
  const [progressMap, setProgressMap] = useState({});
  const [grades, setGrades] = useState([]);
  const [availableTopics, setAvailableTopics] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [activeTab, setActiveTab] = useState('progress');
  const navigate = useNavigate();
  const fullName = localStorage.getItem('full_name');
  const userId = localStorage.getItem('user_id');

  useEffect(() => {
    const fetchData = async () => {
      try {
        const [quizzesData, materialsData, progressData, topicsData] = await Promise.all([
          getQuizzes(),
          getApprovedMaterials(userId),
          getProgressMap(userId),
          getAvailableTopics(userId)
        ]);
        setQuizzes(quizzesData.quizzes || []);
        setMaterials(materialsData.materials || []);
        setProgressMap(progressData.progress_map || {});
        setGrades(progressData.grades || []);
        setAvailableTopics(topicsData.topics || []);
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
        return 'bg-green-100 border-green-500 text-green-800';
      case 'yellow':
        return 'bg-yellow-100 border-yellow-500 text-yellow-800';
      case 'blue':
        return 'bg-blue-100 border-blue-500 text-blue-800';
      case 'gray':
      default:
        return 'bg-gray-100 border-gray-400 text-gray-500';
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

  const getFilteredQuizzes = (topicId) => {
    return quizzes.filter(q => q.topic === availableTopics.find(t => t.topic_id === topicId)?.topic_name);
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-100">
        <div className="text-xl text-gray-600">Loading dashboard...</div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-100">
      <nav className="bg-white shadow-md p-4 sticky top-0 z-10">
        <div className="container mx-auto flex justify-between items-center">
          <h1 className="text-xl font-bold text-blue-600">EDUCARE</h1>
          <div className="flex items-center gap-4">
            <span className="text-gray-600">Welcome, {fullName}</span>
            <button onClick={handleLogout} className="bg-red-500 text-white px-4 py-2 rounded hover:bg-red-600">Logout</button>
          </div>
        </div>
      </nav>

      {/* Tabs */}
      <div className="bg-white border-b">
        <div className="container mx-auto">
          <div className="flex space-x-8">
            <button
              onClick={() => setActiveTab('progress')}
              className={`py-4 px-2 font-medium transition ${
                activeTab === 'progress'
                  ? 'text-blue-600 border-b-2 border-blue-600'
                  : 'text-gray-500 hover:text-gray-700'
              }`}
            >
              Progress Map
            </button>
            <button
              onClick={() => setActiveTab('quizzes')}
              className={`py-4 px-2 font-medium transition ${
                activeTab === 'quizzes'
                  ? 'text-blue-600 border-b-2 border-blue-600'
                  : 'text-gray-500 hover:text-gray-700'
              }`}
            >
              Available Quizzes
            </button>
            <button
              onClick={() => setActiveTab('materials')}
              className={`py-4 px-2 font-medium transition ${
                activeTab === 'materials'
                  ? 'text-blue-600 border-b-2 border-blue-600'
                  : 'text-gray-500 hover:text-gray-700'
              }`}
            >
              Study Materials
            </button>
          </div>
        </div>
      </div>

      <div className="container mx-auto p-6">
        {error && (
          <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded mb-4">
            {error}
          </div>
        )}

        {/* Progress Map Tab */}
        {activeTab === 'progress' && (
          <div>
            <h2 className="text-2xl font-bold mb-2">Topic Progression Map</h2>
            <p className="text-gray-600 mb-6">Track your mastery across all topics. Complete prerequisites to unlock new topics.</p>

            {/* Legend */}
            <div className="flex gap-6 mb-6 flex-wrap">
              <div className="flex items-center gap-2">
                <div className="w-4 h-4 rounded bg-green-500"></div>
                <span className="text-sm text-gray-600">Mastered (70%+)</span>
              </div>
              <div className="flex items-center gap-2">
                <div className="w-4 h-4 rounded bg-yellow-500"></div>
                <span className="text-sm text-gray-600">In Progress</span>
              </div>
              <div className="flex items-center gap-2">
                <div className="w-4 h-4 rounded bg-blue-500"></div>
                <span className="text-sm text-gray-600">Available</span>
              </div>
              <div className="flex items-center gap-2">
                <div className="w-4 h-4 rounded bg-gray-400"></div>
                <span className="text-sm text-gray-600">Locked</span>
              </div>
            </div>

            {/* Progress by Grade */}
            {grades.map((grade) => (
              <div key={grade} className="mb-8">
                <h3 className="text-lg font-semibold mb-3 text-gray-700">Grade {grade}</h3>
                <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
                  {(progressMap[grade] || []).map((topic) => (
                    <div
                      key={topic.topic_id}
                      className={`rounded-lg border-2 p-4 transition ${getColorClasses(topic.color)} ${
                        topic.color === 'blue' ? 'cursor-pointer hover:shadow-md' : ''
                      }`}
                      onClick={() => {
                        if (topic.color === 'blue') {
                          navigate(`/quiz/${quizzes.find(q => q.topic === topic.topic_name)?.quiz_id || ''}`);
                        }
                      }}
                      title={
                        topic.color === 'gray' && topic.prerequisite_names.length > 0
                          ? `Complete ${topic.prerequisite_names.join(', ')} first`
                          : ''
                      }
                    >
                      <div className="flex justify-between items-start mb-2">
                        <h4 className="font-semibold text-sm">{topic.topic_name}</h4>
                        <span className={`text-xs px-2 py-0.5 rounded-full ${
                          topic.color === 'green' ? 'bg-green-200' :
                          topic.color === 'yellow' ? 'bg-yellow-200' :
                          topic.color === 'blue' ? 'bg-blue-200' : 'bg-gray-200'
                        }`}>
                          {getStatusLabel(topic.color)}
                        </span>
                      </div>
                      {topic.avg_score !== null && (
                        <div className="mb-2">
                          <div className="text-xs text-gray-600 mb-1">Score: {topic.avg_score}%</div>
                          <div className="w-full bg-white bg-opacity-50 rounded-full h-2">
                            <div
                              className={`h-2 rounded-full ${
                                topic.avg_score >= 70 ? 'bg-green-500' : 'bg-yellow-500'
                              }`}
                              style={{ width: `${Math.min(topic.avg_score, 100)}%` }}
                            ></div>
                          </div>
                        </div>
                      )}
                      {topic.color === 'gray' && topic.prerequisite_names.length > 0 && (
                        <p className="text-xs mt-2 opacity-75">
                          Complete {topic.prerequisite_names.join(', ')} first
                        </p>
                      )}
                      {topic.color === 'blue' && (
                        <p className="text-xs mt-2">Click to take quiz</p>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            ))}

            {grades.length === 0 && (
              <div className="bg-white rounded-lg shadow-md p-12 text-center">
                <p className="text-gray-500 text-lg">No topics available yet</p>
              </div>
            )}
          </div>
        )}

        {/* Quizzes Tab */}
        {activeTab === 'quizzes' && (
          <div>
            <h2 className="text-2xl font-bold mb-6">Available Quizzes</h2>

            {/* Available (unlocked) topics with quizzes */}
            {availableTopics.filter(t => t.prerequisites_met).length > 0 ? (
              <div className="space-y-6">
                {availableTopics.filter(t => t.prerequisites_met).map((topic) => {
                  const topicQuizzes = quizzes.filter(q => q.topic === topic.topic_name);
                  if (topicQuizzes.length === 0) return null;
                  return (
                    <div key={topic.topic_id} className="bg-white rounded-lg shadow-md p-6">
                      <div className="flex justify-between items-center mb-4">
                        <h3 className="text-lg font-semibold">{topic.topic_name}</h3>
                        <span className={`text-sm px-3 py-1 rounded-full ${
                          topic.status === 'mastered' ? 'bg-green-100 text-green-800' :
                          topic.status === 'in_progress' ? 'bg-yellow-100 text-yellow-800' :
                          'bg-blue-100 text-blue-800'
                        }`}>
                          {topic.status === 'mastered' ? 'Mastered' :
                           topic.status === 'in_progress' ? `In Progress (${topic.avg_score}%)` : 'Not Started'}
                        </span>
                      </div>
                      <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-4">
                        {topicQuizzes.map((quiz) => (
                          <div key={quiz.quiz_id} className="border rounded-lg p-4">
                            <h4 className="font-medium mb-2">{quiz.title}</h4>
                            <p className="text-sm text-gray-500 mb-2">Marks: {quiz.total_marks}</p>
                            <button
                              onClick={() => navigate(`/quiz/${quiz.quiz_id}`)}
                              className="w-full bg-blue-600 text-white py-2 rounded hover:bg-blue-700 text-sm"
                            >
                              Take Quiz
                            </button>
                          </div>
                        ))}
                      </div>
                    </div>
                  );
                })}
              </div>
            ) : (
              <div className="bg-white rounded-lg shadow-md p-12 text-center">
                <p className="text-gray-500 text-lg">No quizzes available</p>
              </div>
            )}

            {/* Locked topics */}
            {availableTopics.filter(t => !t.prerequisites_met).length > 0 && (
              <div className="mt-8">
                <h3 className="text-xl font-semibold mb-4 text-gray-500">Locked Topics</h3>
                <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-4">
                  {availableTopics.filter(t => !t.prerequisites_met).map((topic) => (
                    <div key={topic.topic_id} className="bg-gray-100 rounded-lg p-4 opacity-60">
                      <h4 className="font-medium text-gray-500">{topic.topic_name}</h4>
                      <p className="text-sm text-gray-400 mt-1">Complete prerequisites first</p>
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
            <h2 className="text-2xl font-bold mb-4">Study Materials</h2>
            {materials.length > 0 ? (
              <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
                {materials.map((material) => (
                  <div key={material.material_id} className="bg-white rounded-lg shadow-md p-6">
                    <h3 className="text-lg font-semibold mb-2">{material.title}</h3>
                    <p className="text-sm text-gray-500 mb-2">Topic: {material.topic_name}</p>
                    <p className="text-sm text-gray-500 mb-4">Added: {new Date(material.generated_date).toLocaleDateString()}</p>
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
                <p className="text-gray-500 text-lg">No study materials available</p>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}

export default StudentDashboard;
