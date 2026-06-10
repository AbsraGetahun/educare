import React, { useEffect, useMemo, useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import api, { familyRegister, listLinkableStudents } from '../services/api';

function FamilyRegister() {
  const [fullName, setFullName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [studentId, setStudentId] = useState('');
  const [students, setStudents] = useState([]);
  const [studentsLoading, setStudentsLoading] = useState(true);
  const [studentSearch, setStudentSearch] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();

  useEffect(() => {
    const run = async () => {
      setStudentsLoading(true);
      try {
        const data = await listLinkableStudents();
        setStudents(data.students || []);
      } catch (_) {
        setStudents([]);
      } finally {
        setStudentsLoading(false);
      }
    };
    run();
  }, []);

  const selectedStudent = useMemo(() => {
    const sid = parseInt(studentId, 10);
    if (!sid) return null;
    return students.find((s) => s.user_id === sid) || null;
  }, [studentId, students]);

  const filteredStudents = useMemo(() => {
    const q = studentSearch.trim().toLowerCase();
    if (!q) return students;
    return students.filter((s) => {
      const hay = `${s.full_name || ''} grade ${s.grade_level || ''} section ${s.section || ''}`.toLowerCase();
      return hay.includes(q);
    });
  }, [students, studentSearch]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      if (!studentId) {
        setError('Please select your child to link your family account.');
        return;
      }

      // Send student_id to backend (new flow). Keep api.js familyRegister for back-compat elsewhere.
      const response = await api.post('/api/family/register', {
        full_name: fullName,
        email: email,
        password: password,
        student_id: parseInt(studentId, 10),
        relationship: 'parent',
      });
      const data = response.data;

      if (data.token) {
        localStorage.setItem('token', data.token);
        localStorage.setItem('user_id', data.user_id);
        localStorage.setItem('full_name', data.full_name);
        localStorage.setItem('role', data.role);
        if (data.students) {
          localStorage.setItem('students', JSON.stringify(data.students));
        }
        navigate('/family/dashboard');
        return;
      }
      navigate('/family/login', { state: { message: data.message || 'Account created successfully! You can now login.' } });
    } catch (err) {
      setError(err.response?.data?.error || 'Registration failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 to-teal-50 flex items-center justify-center p-4">
      <div className="w-full max-w-md">
        {/* Header */}
        <div className="text-center mb-8">
          <Link to="/" className="inline-flex items-center justify-center mb-6">
            <div className="w-12 h-12 bg-teal-500 rounded-xl flex items-center justify-center shadow-md">
              <svg className="w-7 h-7 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z" />
              </svg>
            </div>
          </Link>
          <h1 className="text-3xl font-bold text-gray-900 mb-2">Family Registration</h1>
          <p className="text-gray-600">Create an account to monitor your child's progress</p>
        </div>

        {/* Registration Card */}
        <div className="bg-white rounded-2xl shadow-xl p-8">
          {error && (
            <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg mb-6">
              {error}
            </div>
          )}
          
          <form onSubmit={handleSubmit}>
            <div className="mb-6">
              <label className="block text-gray-700 text-sm font-semibold mb-2">Full Name</label>
              <input
                type="text"
                value={fullName}
                onChange={(e) => setFullName(e.target.value)}
                className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-teal-500 focus:border-transparent transition"
                placeholder="John Doe"
                required
              />
            </div>
            
            <div className="mb-6">
              <label className="block text-gray-700 text-sm font-semibold mb-2">Email Address</label>
              <input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-teal-500 focus:border-transparent transition"
                placeholder="parent@educare.com"
                required
              />
            </div>
            
            <div className="mb-6">
              <label className="block text-gray-700 text-sm font-semibold mb-2">Password</label>
              <input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-teal-500 focus:border-transparent transition"
                placeholder="••••••••"
                required
              />
            </div>
            
            <div className="mb-6">
              <label className="block text-gray-700 text-sm font-semibold mb-2">Select Child</label>
              <input
                type="text"
                value={studentSearch}
                onChange={(e) => setStudentSearch(e.target.value)}
                placeholder="Search by name, grade, section..."
                className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-teal-500 focus:border-transparent transition mb-3"
                disabled={studentsLoading || students.length === 0}
              />
              <select
                value={studentId}
                onChange={(e) => setStudentId(e.target.value)}
                className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-teal-500 focus:border-transparent transition bg-white"
                required
                disabled={studentsLoading}
              >
                <option value="">
                  {studentsLoading ? 'Loading students...' : students.length ? 'Select your child' : 'No students found'}
                </option>
                {filteredStudents.map((s) => (
                  <option key={s.user_id} value={s.user_id}>
                    {s.full_name} — Grade {s.grade_level}, Section {s.section}
                  </option>
                ))}
              </select>
              {!studentsLoading && students.length > 0 && filteredStudents.length === 0 && (
                <p className="text-sm text-gray-500 mt-2">No students match your search.</p>
              )}
              {selectedStudent ? (
                <p className="text-sm text-gray-500 mt-1">
                  Linking this family account to <span className="font-semibold">{selectedStudent.full_name}</span>.
                </p>
              ) : (
                <p className="text-sm text-gray-500 mt-1">Choose the student you want to link to this family account.</p>
              )}
            </div>
            
            <button
              type="submit"
              disabled={loading}
              className="w-full bg-teal-500 text-white py-3 rounded-lg font-semibold hover:bg-teal-600 transition disabled:opacity-50 disabled:cursor-not-allowed shadow-lg"
            >
              {loading ? 'Creating account...' : 'Create Account'}
            </button>
          </form>
          
          <div className="mt-6 text-center">
            <p className="text-gray-600">
              Already have an account?{' '}
              <Link to="/family/login" className="text-teal-600 font-semibold hover:text-teal-700">
                Sign in here
              </Link>
            </p>
          </div>
          
          <div className="mt-4 text-center">
            <Link to="/" className="text-gray-500 hover:text-gray-700 text-sm">
              ← Back to portal selection
            </Link>
          </div>
        </div>
      </div>
    </div>
  );
}

export default FamilyRegister;