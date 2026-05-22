import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { useState, useEffect } from 'react';
import LandingPage from './pages/LandingPage';
import StudentLogin from './pages/StudentLogin';
import TeacherLogin from './pages/TeacherLogin';
import FamilyLogin from './pages/FamilyLogin';
import AdminLogin from './pages/AdminLogin';
import StudentRegister from './pages/StudentRegister';
import FamilyRegister from './pages/FamilyRegister';
import StudentDashboard from './pages/StudentDashboard';
import TeacherDashboard from './pages/TeacherDashboard';
import FamilyDashboard from './pages/FamilyDashboard';
import AdminDashboard from './pages/AdminDashboard';
import QuizTaking from './pages/QuizTaking';
function App() {
  const [token, setToken] = useState(localStorage.getItem('token'));
  const [role, setRole] = useState(localStorage.getItem('role'));

  // Update state when localStorage changes
  useEffect(() => {
    const handleStorageChange = () => {
      setToken(localStorage.getItem('token'));
      setRole(localStorage.getItem('role'));
    };

    // Listen for storage events (when localStorage is updated in other tabs)
    window.addEventListener('storage', handleStorageChange);

    // Also check for changes periodically (for same-tab updates)
    const interval = setInterval(() => {
      const currentToken = localStorage.getItem('token');
      const currentRole = localStorage.getItem('role');
      if (currentToken !== token || currentRole !== role) {
        setToken(currentToken);
        setRole(currentRole);
      }
    }, 100);

    return () => {
      window.removeEventListener('storage', handleStorageChange);
      clearInterval(interval);
    };
  }, [token, role]);

  return (
    <Router>
      <Routes>
        {/* Landing Page */}
        <Route path="/" element={<LandingPage />} />
        
        {/* Login Routes */}
        <Route path="/student/login" element={<StudentLogin />} />
        <Route path="/teacher/login" element={<TeacherLogin />} />
        <Route path="/family/login" element={<FamilyLogin />} />
        <Route path="/admin/login" element={<AdminLogin />} />
        
        {/* Registration Routes */}
        <Route path="/student/register" element={<StudentRegister />} />
        <Route path="/family/register" element={<FamilyRegister />} />
        
        {/* Protected Dashboard Routes */}
        <Route 
          path="/student/dashboard" 
          element={token && role === 'student' ? <StudentDashboard /> : <Navigate to="/student/login" />} 
        />
        <Route 
          path="/teacher/dashboard" 
          element={token && role === 'teacher' ? <TeacherDashboard /> : <Navigate to="/teacher/login" />} 
        />
        <Route 
          path="/family/dashboard" 
          element={token && role === 'family' ? <FamilyDashboard /> : <Navigate to="/family/login" />} 
        />
        <Route 
          path="/admin/dashboard" 
          element={token && role === 'admin' ? <AdminDashboard /> : <Navigate to="/admin/login" />} 
        />
        
        {/* Quiz Route */}
        <Route 
          path="/quiz/:quizId" 
          element={token && role === 'student' ? <QuizTaking /> : <Navigate to="/student/login" />} 
        />
        
        {/* Fallback Route */}
        <Route path="*" element={<Navigate to="/" />} />
      </Routes>
    </Router>
  );
}

export default App;
