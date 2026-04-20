import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { LineChart, Line, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, ReferenceLine } from 'recharts';
import { getFamilyStudentProgress, getFamilyStudentGaps, getFamilyStudentRecommendations, getStudentReport } from '../services/api';

function FamilyDashboard() {
  const [students, setStudents] = useState([]);
  const [selectedStudent, setSelectedStudent] = useState(null);
  const [progress, setProgress] = useState([]);
  const [gaps, setGaps] = useState([]);
  const [recommendations, setRecommendations] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [chartType, setChartType] = useState('line');
  const [downloadingReport, setDownloadingReport] = useState(false);
  const navigate = useNavigate();
  const fullName = localStorage.getItem('full_name');

  useEffect(() => {
    const storedStudents = localStorage.getItem('students');
    if (storedStudents) {
      const studentsList = JSON.parse(storedStudents);
      setStudents(studentsList);
      if (studentsList.length > 0) {
        setSelectedStudent(studentsList[0]);
      }
    }
    setLoading(false);
  }, []);

  useEffect(() => {
    if (selectedStudent) {
      fetchStudentData(selectedStudent.student_id);
    }
  }, [selectedStudent]);

  const fetchStudentData = async (studentId) => {
    setLoading(true);
    setError('');
    try {
      const [progressData, gapsData, recommendationsData] = await Promise.all([
        getFamilyStudentProgress(studentId),
        getFamilyStudentGaps(studentId),
        getFamilyStudentRecommendations(studentId)
      ]);
      
      setProgress(progressData.attempts || []);
      setGaps(gapsData.gaps || []);
      setRecommendations(recommendationsData.recommendations || []);
    } catch (err) {
      setError('Failed to load student data');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleLogout = () => {
    localStorage.clear();
    navigate('/family/login');
  };

  const handleStudentChange = (e) => {
    const studentId = parseInt(e.target.value);
    const student = students.find(s => s.student_id === studentId);
    setSelectedStudent(student);
  };

  const handleDownloadReport = async () => {
    if (!selectedStudent) return;
    setDownloadingReport(true);
    try {
      const blob = await getStudentReport(selectedStudent.student_id);
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = `${selectedStudent.full_name}_Report.pdf`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(url);
    } catch (err) {
      setError('Failed to download report');
      console.error(err);
    } finally {
      setDownloadingReport(false);
    }
  };

  const getWeaknessColor = (level) => {
    if (level === 'High') return 'bg-red-100 text-red-800';
    if (level === 'Moderate') return 'bg-yellow-100 text-yellow-800';
    return 'bg-green-100 text-green-800';
  };

  const getWeaknessBadgeColor = (level) => {
    if (level === 'High') return 'bg-red-500';
    if (level === 'Moderate') return 'bg-yellow-500';
    return 'bg-green-500';
  };

  // Prepare chart data sorted by date
  const sortedProgress = [...progress].sort((a, b) => new Date(a.completed_at) - new Date(b.completed_at));
  const chartData = sortedProgress.map((attempt, index) => {
    const pct = Math.round((attempt.score / attempt.total_marks) * 100);
    const date = new Date(attempt.completed_at);
    return {
      name: attempt.quiz_title || `Quiz ${index + 1}`,
      score: attempt.score,
      total: attempt.total_marks,
      percentage: pct,
      date: date.toLocaleDateString(),
      shortDate: `${date.getMonth() + 1}/${date.getDate()}`,
      topic: attempt.topic || ''
    };
  });
  const avgScore = chartData.length > 0
    ? Math.round(chartData.reduce((sum, d) => sum + d.percentage, 0) / chartData.length)
    : 0;

  const CustomTooltip = ({ active, payload }) => {
    if (active && payload && payload.length) {
      const data = payload[0].payload;
      return (
        <div className="bg-white border border-gray-200 rounded-lg shadow-lg p-3">
          <p className="font-semibold text-gray-800">{data.name}</p>
          <p className="text-sm text-gray-500">{data.topic}</p>
          <p className="text-sm text-gray-500">{data.date}</p>
          <div className="mt-1 pt-1 border-t">
            <p className="text-sm">
              Score: <span className="font-bold">{data.score}/{data.total}</span>
              <span className={`ml-2 font-bold ${data.percentage >= 70 ? 'text-green-600' : data.percentage >= 40 ? 'text-yellow-600' : 'text-red-600'}`}>
                ({data.percentage}%)
              </span>
            </p>
          </div>
        </div>
      );
    }
    return null;
  };

  if (loading && !selectedStudent) {
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
            <span className="text-gray-600">Family Portal</span>
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

      {/* Content */}
      <div className="container mx-auto p-6">
        {error && (
          <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded mb-4">
            {error}
          </div>
        )}

        {/* Child Selector */}
        {students.length > 1 && (
          <div className="bg-white rounded-lg shadow-md p-6 mb-6">
            <label className="block text-gray-700 text-sm font-bold mb-2">
              Select Child
            </label>
            <select
              value={selectedStudent?.student_id || ''}
              onChange={handleStudentChange}
              className="w-full md:w-64 px-3 py-2 border border-gray-300 rounded focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              {students.map((student) => (
                <option key={student.student_id} value={student.student_id}>
                  {student.full_name} - Grade {student.grade_level}, Section {student.section}
                </option>
              ))}
            </select>
          </div>
        )}

        {selectedStudent && (
          <>
            {/* Student Info Card */}
            <div className="bg-white rounded-lg shadow-md p-6 mb-6">
              <div className="flex flex-wrap justify-between items-start mb-4 gap-4">
                <h2 className="text-2xl font-bold">Student Information</h2>
                <button
                  onClick={handleDownloadReport}
                  disabled={downloadingReport}
                  className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 transition flex items-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                    <path strokeLinecap="round" strokeLinejoin="round" d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                  </svg>
                  {downloadingReport ? 'Downloading...' : 'Download Report'}
                </button>
              </div>
              <div className="grid md:grid-cols-3 gap-4">
                <div>
                  <div className="text-sm text-gray-500">Name</div>
                  <div className="text-lg font-semibold">{selectedStudent.full_name}</div>
                </div>
                <div>
                  <div className="text-sm text-gray-500">Grade</div>
                  <div className="text-lg font-semibold">{selectedStudent.grade_level}</div>
                </div>
                <div>
                  <div className="text-sm text-gray-500">Section</div>
                  <div className="text-lg font-semibold">{selectedStudent.section}</div>
                </div>
              </div>
            </div>

            {/* Performance Trend */}
            <div className="bg-white rounded-lg shadow-md p-6 mb-6">
              <div className="flex flex-wrap justify-between items-center mb-4 gap-2">
                <div>
                  <h2 className="text-2xl font-bold">Performance Trend</h2>
                  {chartData.length > 0 && (
                    <p className="text-sm text-gray-500 mt-1">
                      {chartData.length} quiz{chartData.length !== 1 ? 'es' : ''} taken
                      {avgScore > 0 && <span> - Average: <span className={`font-semibold ${avgScore >= 70 ? 'text-green-600' : avgScore >= 40 ? 'text-yellow-600' : 'text-red-600'}`}>{avgScore}%</span></span>}
                    </p>
                  )}
                </div>
                <div className="flex bg-gray-100 rounded-lg p-1">
                  <button
                    onClick={() => setChartType('line')}
                    className={`px-4 py-1.5 rounded-md text-sm font-medium transition ${
                      chartType === 'line'
                        ? 'bg-white shadow text-blue-600'
                        : 'text-gray-500 hover:text-gray-700'
                    }`}
                  >
                    Line
                  </button>
                  <button
                    onClick={() => setChartType('bar')}
                    className={`px-4 py-1.5 rounded-md text-sm font-medium transition ${
                      chartType === 'bar'
                        ? 'bg-white shadow text-blue-600'
                        : 'text-gray-500 hover:text-gray-700'
                    }`}
                  >
                    Bar
                  </button>
                </div>
              </div>
              {chartData.length > 0 ? (
                <div className="h-80">
                  <ResponsiveContainer width="100%" height={300}>
                    {chartType === 'line' ? (
                      <LineChart data={chartData}>
                        <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
                        <XAxis
                          dataKey="shortDate"
                          tick={{ fontSize: 12 }}
                          tickLine={false}
                        />
                        <YAxis
                          domain={[0, 100]}
                          tick={{ fontSize: 12 }}
                          tickLine={false}
                          tickFormatter={(v) => `${v}%`}
                        />
                        <Tooltip content={<CustomTooltip />} />
                        <Legend />
                        <ReferenceLine
                          y={avgScore}
                          stroke="#9ca3af"
                          strokeDasharray="5 5"
                          label={{ value: `Avg ${avgScore}%`, position: 'right', fill: '#6b7280', fontSize: 12 }}
                        />
                        <ReferenceLine y={70} stroke="#10b981" strokeDasharray="3 3" strokeOpacity={0.4} />
                        <Line
                          type="monotone"
                          dataKey="percentage"
                          stroke="#3B82F6"
                          strokeWidth={2}
                          name="Score %"
                          dot={{ fill: '#3B82F6', strokeWidth: 2, r: 4 }}
                          activeDot={{ r: 6, fill: '#2563eb' }}
                        />
                      </LineChart>
                    ) : (
                      <BarChart data={chartData}>
                        <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
                        <XAxis
                          dataKey="shortDate"
                          tick={{ fontSize: 12 }}
                          tickLine={false}
                        />
                        <YAxis
                          domain={[0, 100]}
                          tick={{ fontSize: 12 }}
                          tickLine={false}
                          tickFormatter={(v) => `${v}%`}
                        />
                        <Tooltip content={<CustomTooltip />} />
                        <Legend />
                        <ReferenceLine
                          y={avgScore}
                          stroke="#9ca3af"
                          strokeDasharray="5 5"
                          label={{ value: `Avg ${avgScore}%`, position: 'right', fill: '#6b7280', fontSize: 12 }}
                        />
                        <ReferenceLine y={70} stroke="#10b981" strokeDasharray="3 3" strokeOpacity={0.4} />
                        <Bar
                          dataKey="percentage"
                          name="Score %"
                          fill="#3B82F6"
                          radius={[4, 4, 0, 0]}
                        />
                      </BarChart>
                    )}
                  </ResponsiveContainer>
                </div>
              ) : (
                <div className="text-gray-500 text-center py-12">
                  <div className="text-4xl mb-2">--</div>
                  No quiz attempts yet
                </div>
              )}
            </div>

            {/* Skill Gaps */}
            <div className="bg-white rounded-lg shadow-md p-6 mb-6">
              <h2 className="text-2xl font-bold mb-4">Skill Gaps</h2>
              {gaps.length > 0 ? (
                <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-4">
                  {gaps.map((gap) => (
                    <div key={gap.topic_id} className="border rounded-lg p-4">
                      <div className="flex justify-between items-start mb-2">
                        <span className="font-semibold text-gray-800">{gap.topic_name}</span>
                        <span className={`px-2 py-1 rounded text-xs font-medium ${getWeaknessColor(gap.weakness_level)}`}>
                          {gap.weakness_level} Need
                        </span>
                      </div>
                      <div className="mt-2">
                        <div className="text-sm text-gray-500 mb-1">Average Score</div>
                        <div className="flex items-center gap-2">
                          <div className="flex-1 bg-gray-200 rounded-full h-2">
                            <div 
                              className={`h-2 rounded-full ${getWeaknessBadgeColor(gap.weakness_level)}`}
                              style={{ width: `${gap.avg_score}%` }}
                            ></div>
                          </div>
                          <span className="text-sm font-medium">{gap.avg_score}%</span>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="text-gray-500 text-center py-8">
                  No skill gaps detected. Great job!
                </div>
              )}
            </div>

            {/* Recommended Practice */}
            <div className="bg-white rounded-lg shadow-md p-6">
              <h2 className="text-2xl font-bold mb-4">Recommended Practice</h2>
              {recommendations.length > 0 ? (
                <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-4">
                  {recommendations.map((rec, index) => (
                    <div key={index} className="border rounded-lg p-4 hover:shadow-md transition">
                      <h3 className="font-semibold text-gray-800 mb-2">{rec.title}</h3>
                      <div className="space-y-1 text-sm text-gray-600">
                        <div className="flex justify-between">
                          <span>Topic:</span>
                          <span className="font-medium">{rec.topic_name}</span>
                        </div>
                        <div className="flex justify-between">
                          <span>Total Marks:</span>
                          <span className="font-medium">{rec.total_marks}</span>
                        </div>
                        <div className="flex justify-between">
                          <span>Current Avg:</span>
                          <span className={`font-medium ${
                            rec.avg_score < 40 ? 'text-red-600' : 
                            rec.avg_score < 70 ? 'text-yellow-600' : 'text-green-600'
                          }`}>
                            {rec.avg_score}%
                          </span>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="text-gray-500 text-center py-8">
                  No recommendations available at this time
                </div>
              )}
            </div>
          </>
        )}
      </div>
    </div>
  );
}

export default FamilyDashboard;
