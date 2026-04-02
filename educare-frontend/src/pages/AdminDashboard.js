import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { adminGetUsers, adminGetUsersByRole, adminCreateUser, adminUpdateUser, adminDeleteUser, adminGetStats, getStudents } from '../services/api';

function AdminDashboard() {
  const [activeTab, setActiveTab] = useState('overview');
  const [users, setUsers] = useState([]);
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [showAddUser, setShowAddUser] = useState(false);
  const [showEditUser, setShowEditUser] = useState(false);
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);
  const [selectedUser, setSelectedUser] = useState(null);
  const [filterRole, setFilterRole] = useState('all');
  const [searchTerm, setSearchTerm] = useState('');
  const [studentsList, setStudentsList] = useState([]);
  const navigate = useNavigate();
  const fullName = localStorage.getItem('full_name');

  const [userForm, setUserForm] = useState({
    full_name: '',
    email: '',
    password: '',
    role: 'student',
    grade_level: '',
    section: '',
    qualification: '',
    subject: '',
    student_ids: [],
    relationship: 'parent'
  });

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    setLoading(true);
    try {
      const [usersData, statsData] = await Promise.all([
        adminGetUsers(),
        adminGetStats()
      ]);
      setUsers(usersData.users || []);
      setStats(statsData);
    } catch (err) {
      setError('Failed to load data');
    } finally {
      setLoading(false);
    }
  };

  const handleFilterChange = async (role) => {
    setFilterRole(role);
    setLoading(true);
    try {
      if (role === 'all') {
        const usersData = await adminGetUsers();
        setUsers(usersData.users || []);
      } else {
        const usersData = await adminGetUsersByRole(role);
        setUsers(usersData.users || []);
      }
    } catch (err) {
      setError('Failed to filter users');
    } finally {
      setLoading(false);
    }
  };

  const handleAddUser = async (e) => {
    e.preventDefault();
    setError('');
    setSuccess('');
    try {
      await adminCreateUser(userForm);
      setSuccess('User created successfully!');
      setShowAddUser(false);
      resetForm();
      fetchData();
    } catch (err) {
      setError(err.response?.data?.error || 'Failed to create user');
    }
  };

  const handleEditUser = async (e) => {
    e.preventDefault();
    setError('');
    setSuccess('');
    try {
      await adminUpdateUser(selectedUser.user_id, userForm);
      setSuccess('User updated successfully!');
      setShowEditUser(false);
      setSelectedUser(null);
      resetForm();
      fetchData();
    } catch (err) {
      setError(err.response?.data?.error || 'Failed to update user');
    }
  };

  const handleDeleteUser = async () => {
    setError('');
    setSuccess('');
    try {
      await adminDeleteUser(selectedUser.user_id);
      setSuccess('User deleted successfully!');
      setShowDeleteConfirm(false);
      setSelectedUser(null);
      fetchData();
    } catch (err) {
      setError(err.response?.data?.error || 'Failed to delete user');
    }
  };

  const openEditModal = (user) => {
    setSelectedUser(user);
    setUserForm({
      full_name: user.full_name,
      email: user.email,
      password: '',
      role: user.role,
      grade_level: user.grade_level || '',
      section: user.section || '',
      qualification: user.qualification || '',
      subject: user.subject || '',
      student_ids: [],
      relationship: 'parent'
    });
    setShowEditUser(true);
  };

  const openDeleteConfirm = (user) => {
    setSelectedUser(user);
    setShowDeleteConfirm(true);
  };

  const resetForm = () => {
    setUserForm({
      full_name: '',
      email: '',
      password: '',
      role: 'student',
      grade_level: '',
      section: '',
      qualification: '',
      subject: '',
      student_ids: [],
      relationship: 'parent'
    });
  };

  const handleLogout = () => {
    localStorage.clear();
    navigate('/admin/login');
  };

  const loadStudents = async () => {
    try {
      const data = await getStudents();
      setStudentsList(data.students || []);
    } catch (err) {
      // silently fail - students list will be empty
    }
  };

  const filteredUsers = users.filter(user =>
    user.full_name.toLowerCase().includes(searchTerm.toLowerCase()) ||
    user.email.toLowerCase().includes(searchTerm.toLowerCase())
  );

  const getRoleBadgeColor = (role) => {
    switch (role) {
      case 'admin': return 'bg-purple-100 text-purple-700';
      case 'teacher': return 'bg-blue-100 text-blue-700';
      case 'student': return 'bg-green-100 text-green-700';
      case 'family': return 'bg-amber-100 text-amber-700';
      default: return 'bg-gray-100 text-gray-700';
    }
  };

  if (loading && !stats) {
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
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
              </svg>
            </div>
            <span className="text-base font-bold text-gray-900">EDUCARE</span>
            <span className="text-[10px] font-medium text-[#2563eb] bg-blue-50 px-1.5 py-0.5 rounded">Admin</span>
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

      <div className="max-w-7xl mx-auto px-4 py-4">
        {/* Messages */}
        {error && (
          <div className="bg-red-50 border border-red-200 text-red-700 px-3 py-2 rounded-lg mb-4 text-sm">
            {error}
            <button onClick={() => setError('')} className="float-right text-red-500 hover:text-red-700">&times;</button>
          </div>
        )}
        {success && (
          <div className="bg-green-50 border border-green-200 text-green-700 px-3 py-2 rounded-lg mb-4 text-sm">
            {success}
            <button onClick={() => setSuccess('')} className="float-right text-green-500 hover:text-green-700">&times;</button>
          </div>
        )}

        {/* Stats Cards */}
        {stats && (
          <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-3 mb-4">
            {[
              { label: 'Students', value: stats.users_by_role?.student || 0, color: 'text-green-600' },
              { label: 'Teachers', value: stats.users_by_role?.teacher || 0, color: 'text-blue-600' },
              { label: 'Families', value: stats.users_by_role?.family || 0, color: 'text-amber-600' },
              { label: 'Admins', value: stats.users_by_role?.admin || 0, color: 'text-purple-600' },
              { label: 'Quizzes', value: stats.total_quizzes || 0, color: 'text-indigo-600' },
              { label: 'Avg Score', value: `${stats.average_score || 0}%`, color: 'text-pink-600' },
            ].map((stat) => (
              <div key={stat.label} className="bg-white rounded-lg shadow-sm p-3">
                <div className="text-[10px] font-medium text-gray-500 uppercase tracking-wide">{stat.label}</div>
                <div className={`text-2xl font-bold ${stat.color} mt-1`}>{stat.value}</div>
              </div>
            ))}
          </div>
        )}

        {/* Tabs */}
        <div className="bg-white border-b border-gray-200 rounded-t-lg">
          <div className="flex gap-1 px-4">
            <button
              onClick={() => setActiveTab('overview')}
              className={`py-2.5 px-4 text-sm font-medium transition border-b-2 ${
                activeTab === 'overview'
                  ? 'text-[#2563eb] border-[#2563eb]'
                  : 'text-gray-500 border-transparent hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              User Management
            </button>
          </div>
        </div>

        {/* User Management */}
        {activeTab === 'overview' && (
          <div className="bg-white rounded-b-lg shadow-sm">
            {/* Filters and Search */}
            <div className="px-4 pt-3 pb-3 border-b border-gray-100 flex flex-col sm:flex-row justify-between items-start sm:items-center gap-3">
              <div className="flex gap-1.5 flex-wrap">
                {[
                  { key: 'all', label: 'All', activeColor: 'bg-[#2563eb] text-white' },
                  { key: 'student', label: 'Students', activeColor: 'bg-green-600 text-white' },
                  { key: 'teacher', label: 'Teachers', activeColor: 'bg-blue-600 text-white' },
                  { key: 'family', label: 'Families', activeColor: 'bg-amber-600 text-white' },
                  { key: 'admin', label: 'Admins', activeColor: 'bg-purple-600 text-white' },
                ].map((btn) => (
                  <button
                    key={btn.key}
                    onClick={() => handleFilterChange(btn.key)}
                    className={`px-3 py-1.5 rounded-md text-xs font-medium transition ${
                      filterRole === btn.key
                        ? btn.activeColor
                        : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                    }`}
                  >
                    {btn.label}
                  </button>
                ))}
              </div>
              <div className="flex gap-2 w-full sm:w-auto">
                <input
                  type="text"
                  placeholder="Search..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  className="px-3 py-1.5 border border-gray-200 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent w-full sm:w-48"
                />
                <button
                  onClick={() => { resetForm(); setShowAddUser(true); loadStudents(); }}
                  className="bg-[#2563eb] text-white px-3 py-1.5 rounded-md text-sm font-medium hover:bg-[#1d4ed8] transition whitespace-nowrap"
                >
                  + Add User
                </button>
              </div>
            </div>

            {/* Users Table */}
            <div className="overflow-x-auto">
              <table className="min-w-full">
                <thead>
                  <tr className="bg-gray-50 border-b border-gray-100">
                    <th className="px-3 py-2 text-left text-[10px] font-semibold text-gray-500 uppercase tracking-wider">ID</th>
                    <th className="px-3 py-2 text-left text-[10px] font-semibold text-gray-500 uppercase tracking-wider">Name</th>
                    <th className="px-3 py-2 text-left text-[10px] font-semibold text-gray-500 uppercase tracking-wider">Email</th>
                    <th className="px-3 py-2 text-left text-[10px] font-semibold text-gray-500 uppercase tracking-wider">Role</th>
                    <th className="px-3 py-2 text-left text-[10px] font-semibold text-gray-500 uppercase tracking-wider">Created</th>
                    <th className="px-3 py-2 text-left text-[10px] font-semibold text-gray-500 uppercase tracking-wider">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-100">
                  {filteredUsers.length === 0 ? (
                    <tr>
                      <td colSpan="6" className="px-3 py-6 text-center text-gray-400 text-sm">
                        No users found
                      </td>
                    </tr>
                  ) : (
                    filteredUsers.map((user, idx) => (
                      <tr key={user.user_id} className={idx % 2 === 0 ? 'bg-white' : 'bg-gray-50/50'}>
                        <td className="px-3 py-2 text-sm text-gray-500">{user.user_id}</td>
                        <td className="px-3 py-2 text-sm font-medium text-gray-900">{user.full_name}</td>
                        <td className="px-3 py-2 text-sm text-gray-500">{user.email}</td>
                        <td className="px-3 py-2">
                          <span className={`px-2 py-0.5 text-[10px] font-semibold rounded-full ${getRoleBadgeColor(user.role)}`}>
                            {user.role}
                          </span>
                        </td>
                        <td className="px-3 py-2 text-xs text-gray-400">
                          {user.created_at ? new Date(user.created_at).toLocaleDateString() : 'N/A'}
                        </td>
                        <td className="px-3 py-2">
                          <div className="flex gap-2">
                            <button
                              onClick={() => openEditModal(user)}
                              className="text-[#2563eb] hover:text-[#1d4ed8] text-xs font-medium"
                            >
                              Edit
                            </button>
                            <button
                              onClick={() => openDeleteConfirm(user)}
                              className="text-red-500 hover:text-red-700 text-xs font-medium"
                            >
                              Delete
                            </button>
                          </div>
                        </td>
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
                      </div>
                    </div>
                  )}
                  {userForm.role === 'family' && (
                    <>
                      <div>
                        <label className="block text-xs font-semibold text-gray-600 mb-1">Relationship</label>
                        <select
                          value={userForm.relationship}
                          onChange={(e) => setUserForm({ ...userForm, relationship: e.target.value })}
                          className="w-full px-3 py-1.5 border border-gray-200 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                        >
                          <option value="parent">Parent</option>
                          <option value="guardian">Guardian</option>
                          <option value="sibling">Sibling</option>
                        </select>
                      </div>
                      <div>
                        <label className="block text-xs font-semibold text-gray-600 mb-1">Link to Student(s) *</label>
                        {studentsList.length === 0 ? (
                          <p className="text-xs text-gray-400 py-2">No students available. Add students first.</p>
                        ) : (
                          <div className="border border-gray-200 rounded-md max-h-40 overflow-y-auto">
                            {studentsList.map((student) => (
                              <label key={student.user_id} className="flex items-center gap-2 px-3 py-1.5 hover:bg-gray-50 cursor-pointer border-b border-gray-100 last:border-0">
                                <input
                                  type="checkbox"
                                  checked={userForm.student_ids.includes(student.user_id)}
                                  onChange={(e) => {
                                    if (e.target.checked) {
                                      setUserForm({ ...userForm, student_ids: [...userForm.student_ids, student.user_id] });
                                    } else {
                                      setUserForm({ ...userForm, student_ids: userForm.student_ids.filter(id => id !== student.user_id) });
                                    }
                                  }}
                                  className="rounded border-gray-300 text-[#2563eb] focus:ring-blue-500"
                                />
                                <span className="text-sm text-gray-700">{student.full_name}</span>
                                <span className="text-[10px] text-gray-400 ml-auto">Grade {student.grade_level}-{student.section}</span>
                              </label>
                            ))}
                          </div>
                        )}
                        {userForm.student_ids.length > 0 && (
                          <p className="text-[10px] text-gray-500 mt-1">{userForm.student_ids.length} student(s) selected</p>
                        )}
                      </div>
                    </>
                  )}
                </div>

      {/* Add User Modal */}
      {showAddUser && (
        <div className="fixed inset-0 bg-black/40 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-xl shadow-xl max-w-md w-full max-h-[85vh] overflow-y-auto">
            <div className="p-4">
              <div className="flex justify-between items-center mb-3">
                <h3 className="text-base font-bold text-gray-900">Add New User</h3>
                <button onClick={() => { setShowAddUser(false); resetForm(); }} className="text-gray-400 hover:text-gray-600">
                  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M6 18L18 6M6 6l12 12" />
                  </svg>
                </button>
              </div>
              <form onSubmit={handleAddUser}>
                <div className="space-y-3">
                  <div>
                    <label className="block text-xs font-semibold text-gray-600 mb-1">Full Name *</label>
                    <input
                      type="text"
                      value={userForm.full_name}
                      onChange={(e) => setUserForm({ ...userForm, full_name: e.target.value })}
                      className="w-full px-3 py-1.5 border border-gray-200 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                      required
                    />
                  </div>
                  <div>
                    <label className="block text-xs font-semibold text-gray-600 mb-1">Email *</label>
                    <input
                      type="email"
                      value={userForm.email}
                      onChange={(e) => setUserForm({ ...userForm, email: e.target.value })}
                      className="w-full px-3 py-1.5 border border-gray-200 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                      required
                    />
                  </div>
                  <div>
                    <label className="block text-xs font-semibold text-gray-600 mb-1">Password *</label>
                    <input
                      type="password"
                      value={userForm.password}
                      onChange={(e) => setUserForm({ ...userForm, password: e.target.value })}
                      className="w-full px-3 py-1.5 border border-gray-200 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                      required
                    />
                  </div>
                  <div>
                    <label className="block text-xs font-semibold text-gray-600 mb-1">Role *</label>
                    <select
                      value={userForm.role}
                      onChange={(e) => setUserForm({ ...userForm, role: e.target.value })}
                      className="w-full px-3 py-1.5 border border-gray-200 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                      required
                    >
                      <option value="student">Student</option>
                      <option value="teacher">Teacher</option>
                      <option value="family">Family</option>
                      <option value="admin">Admin</option>
                    </select>
                  </div>
                  {userForm.role === 'student' && (
                    <>
                      <div>
                        <label className="block text-xs font-semibold text-gray-600 mb-1">Grade Level *</label>
                        <input
                          type="text"
                          value={userForm.grade_level}
                          onChange={(e) => setUserForm({ ...userForm, grade_level: e.target.value })}
                          className="w-full px-3 py-1.5 border border-gray-200 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                          required
                        />
                      </div>
                      <div>
                        <label className="block text-xs font-semibold text-gray-600 mb-1">Section *</label>
                        <input
                          type="text"
                          value={userForm.section}
                          onChange={(e) => setUserForm({ ...userForm, section: e.target.value })}
                          className="w-full px-3 py-1.5 border border-gray-200 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                          required
                        />
                      </div>
                    </>
                  )}
                  {userForm.role === 'teacher' && (
                    <>
                      <div>
                        <label className="block text-xs font-semibold text-gray-600 mb-1">Qualification *</label>
                        <input
                          type="text"
                          value={userForm.qualification}
                          onChange={(e) => setUserForm({ ...userForm, qualification: e.target.value })}
                          className="w-full px-3 py-1.5 border border-gray-200 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                          required
                        />
                      </div>
                      <div>
                        <label className="block text-xs font-semibold text-gray-600 mb-1">Subject *</label>
                        <input
                          type="text"
                          value={userForm.subject}
                          onChange={(e) => setUserForm({ ...userForm, subject: e.target.value })}
                          className="w-full px-3 py-1.5 border border-gray-200 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                          required
                        />
                      </div>
                    </>
                  )}
                </div>
                <div className="flex justify-end gap-2 mt-4">
                  <button
                    type="button"
                    onClick={() => { setShowAddUser(false); resetForm(); }}
                    className="px-3 py-1.5 border border-gray-200 rounded-md text-sm text-gray-600 hover:bg-gray-50 transition"
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    className="px-3 py-1.5 bg-[#2563eb] text-white rounded-md text-sm font-medium hover:bg-[#1d4ed8] transition"
                  >
                    Add User
                  </button>
                </div>
              </form>
            </div>
          </div>
        </div>
      )}

      {/* Edit User Modal */}
      {showEditUser && selectedUser && (
        <div className="fixed inset-0 bg-black/40 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-xl shadow-xl max-w-md w-full max-h-[85vh] overflow-y-auto">
            <div className="p-4">
              <div className="flex justify-between items-center mb-3">
                <h3 className="text-base font-bold text-gray-900">Edit User</h3>
                <button onClick={() => { setShowEditUser(false); setSelectedUser(null); resetForm(); }} className="text-gray-400 hover:text-gray-600">
                  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M6 18L18 6M6 6l12 12" />
                  </svg>
                </button>
              </div>
              <form onSubmit={handleEditUser}>
                <div className="space-y-3">
                  <div>
                    <label className="block text-xs font-semibold text-gray-600 mb-1">Full Name *</label>
                    <input
                      type="text"
                      value={userForm.full_name}
                      onChange={(e) => setUserForm({ ...userForm, full_name: e.target.value })}
                      className="w-full px-3 py-1.5 border border-gray-200 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                      required
                    />
                  </div>
                  <div>
                    <label className="block text-xs font-semibold text-gray-600 mb-1">Email *</label>
                    <input
                      type="email"
                      value={userForm.email}
                      onChange={(e) => setUserForm({ ...userForm, email: e.target.value })}
                      className="w-full px-3 py-1.5 border border-gray-200 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                      required
                    />
                  </div>
                  <div>
                    <label className="block text-xs font-semibold text-gray-600 mb-1">Password (blank = keep current)</label>
                    <input
                      type="password"
                      value={userForm.password}
                      onChange={(e) => setUserForm({ ...userForm, password: e.target.value })}
                      className="w-full px-3 py-1.5 border border-gray-200 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    />
                  </div>
                  <div>
                    <label className="block text-xs font-semibold text-gray-600 mb-1">Role *</label>
                    <select
                      value={userForm.role}
                      onChange={(e) => setUserForm({ ...userForm, role: e.target.value })}
                      className="w-full px-3 py-1.5 border border-gray-200 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                      required
                    >
                      <option value="student">Student</option>
                      <option value="teacher">Teacher</option>
                      <option value="family">Family</option>
                      <option value="admin">Admin</option>
                    </select>
                  </div>
                  {userForm.role === 'student' && (
                    <>
                      <div>
                        <label className="block text-xs font-semibold text-gray-600 mb-1">Grade Level *</label>
                        <input
                          type="text"
                          value={userForm.grade_level}
                          onChange={(e) => setUserForm({ ...userForm, grade_level: e.target.value })}
                          className="w-full px-3 py-1.5 border border-gray-200 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                          required
                        />
                      </div>
                      <div>
                        <label className="block text-xs font-semibold text-gray-600 mb-1">Section *</label>
                        <input
                          type="text"
                          value={userForm.section}
                          onChange={(e) => setUserForm({ ...userForm, section: e.target.value })}
                          className="w-full px-3 py-1.5 border border-gray-200 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                          required
                        />
                      </div>
                    </>
                  )}
                  {userForm.role === 'teacher' && (
                    <>
                      <div>
                        <label className="block text-xs font-semibold text-gray-600 mb-1">Qualification *</label>
                        <input
                          type="text"
                          value={userForm.qualification}
                          onChange={(e) => setUserForm({ ...userForm, qualification: e.target.value })}
                          className="w-full px-3 py-1.5 border border-gray-200 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                          required
                        />
                      </div>
                      <div>
                        <label className="block text-xs font-semibold text-gray-600 mb-1">Subject *</label>
                        <input
                          type="text"
                          value={userForm.subject}
                          onChange={(e) => setUserForm({ ...userForm, subject: e.target.value })}
                          className="w-full px-3 py-1.5 border border-gray-200 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                          required
                        />
                      </div>
                    </>
                  )}
                </div>
                <div className="flex justify-end gap-2 mt-4">
                  <button
                    type="button"
                    onClick={() => { setShowEditUser(false); setSelectedUser(null); resetForm(); }}
                    className="px-3 py-1.5 border border-gray-200 rounded-md text-sm text-gray-600 hover:bg-gray-50 transition"
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    className="px-3 py-1.5 bg-[#2563eb] text-white rounded-md text-sm font-medium hover:bg-[#1d4ed8] transition"
                  >
                    Update User
                  </button>
                </div>
              </form>
            </div>
          </div>
        </div>
      )}

      {/* Delete Confirmation Modal */}
      {showDeleteConfirm && selectedUser && (
        <div className="fixed inset-0 bg-black/40 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-xl shadow-xl max-w-sm w-full">
            <div className="p-4 text-center">
              <div className="mx-auto w-10 h-10 rounded-full bg-red-100 flex items-center justify-center mb-3">
                <svg className="w-5 h-5 text-red-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                </svg>
              </div>
              <h3 className="text-base font-bold text-gray-900 mb-1">Delete User</h3>
              <p className="text-sm text-gray-500 mb-4">
                Are you sure you want to delete <strong>{selectedUser.full_name}</strong>? This cannot be undone.
              </p>
              <div className="flex justify-center gap-2">
                <button
                  onClick={() => { setShowDeleteConfirm(false); setSelectedUser(null); }}
                  className="px-4 py-1.5 border border-gray-200 rounded-md text-sm text-gray-600 hover:bg-gray-50 transition"
                >
                  Cancel
                </button>
                <button
                  onClick={handleDeleteUser}
                  className="px-4 py-1.5 bg-red-600 text-white rounded-md text-sm font-medium hover:bg-red-700 transition"
                >
                  Delete
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default AdminDashboard;
