import React, { useEffect, useState, useMemo } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { getProfile, updateProfile, changePassword, uploadProfilePicture } from '../services/api';
import { validatePassword } from '../utils/passwordRules';

function Profile() {
  const [profile, setProfile] = useState(null);
  const [loading, setLoading] = useState(true);
  const [msg, setMsg] = useState('');
  const [err, setErr] = useState('');
  const navigate = useNavigate();

  // Edit profile
  const [fullName, setFullName] = useState('');
  const [email, setEmail] = useState('');
  const [saving, setSaving] = useState(false);

  // Change pw
  const [oldPw, setOldPw] = useState('');
  const [newPw, setNewPw] = useState('');
  const [confirmPw, setConfirmPw] = useState('');
  const [showPw, setShowPw] = useState(false);
  const [pwSaving, setPwSaving] = useState(false);
  const pwVal = useMemo(() => validatePassword(newPw), [newPw]);

  // Pic upload
  const [uploading, setUploading] = useState(false);

  useEffect(() => {
    const token = localStorage.getItem('token');
    if (!token) {
      navigate('/student/login');
      return;
    }
    loadProfile();
  }, [navigate]);

  const loadProfile = async () => {
    try {
      const data = await getProfile();
      setProfile(data);
      setFullName(data.full_name || '');
      setEmail(data.email || '');
    } catch (e) {
      setErr('Failed to load profile');
    } finally {
      setLoading(false);
    }
  };

  const handleUpdateProfile = async (e) => {
    e.preventDefault();
    setErr(''); setMsg(''); setSaving(true);
    try {
      await updateProfile(fullName, email);
      setMsg('Profile updated successfully');
      await loadProfile();
    } catch (e) {
      setErr(e.response?.data?.error || 'Update failed');
    } finally {
      setSaving(false);
    }
  };

  const handleChangePassword = async (e) => {
    e.preventDefault();
    setErr(''); setMsg('');
    if (newPw !== confirmPw) { setErr('New passwords do not match'); return; }
    if (!pwVal.isValid) { setErr('New password is not strong enough'); return; }
    setPwSaving(true);
    try {
      await changePassword(oldPw, newPw, confirmPw);
      setMsg('Password changed successfully');
      setOldPw(''); setNewPw(''); setConfirmPw('');
    } catch (e) {
      setErr(e.response?.data?.error || 'Password change failed');
    } finally {
      setPwSaving(false);
    }
  };

  const handlePicUpload = async (e) => {
    const file = e.target.files[0];
    if (!file) return;
    if (!['image/jpeg','image/png','image/gif'].includes(file.type)) {
      setErr('Only JPG, PNG, GIF allowed');
      return;
    }
    setUploading(true); setErr(''); setMsg('');
    try {
      const res = await uploadProfilePicture(file);
      setMsg('Profile picture updated');
      setProfile(p => ({...p, profile_picture: res.profile_picture}));
    } catch (e) {
      setErr(e.response?.data?.error || 'Upload failed (max 20MB)');
    } finally {
      setUploading(false);
      e.target.value = '';
    }
  };

  const handleSignOut = () => {
    localStorage.clear();
    navigate('/');
  };

  if (loading) return (
    <div className="min-h-screen bg-[#F3F4F6] flex items-center justify-center">
      <div className="flex items-center gap-3">
        <div className="w-5 h-5 border-2 border-teal-500 border-t-transparent rounded-full animate-spin"></div>
        <span className="text-gray-500 text-sm">Loading profile...</span>
      </div>
    </div>
  );

  const picUrl = profile?.profile_picture ? `http://localhost:5000${profile.profile_picture}` : null;

  return (
    <div className="min-h-screen bg-[#F3F4F6]">
      {/* Top Bar */}
      <div className="bg-white border-b border-gray-200">
        <div className="max-w-5xl mx-auto px-5 py-3 flex justify-between items-center">
          <Link to="/student/dashboard" className="text-teal-600 hover:text-teal-700 text-sm font-medium flex items-center gap-1">
            ← Back
          </Link>
          <div className="flex items-center gap-3">
            <span className="text-sm text-gray-600 hidden sm:block">{profile?.full_name}</span>
            <button onClick={handleSignOut} className="text-sm text-red-600 hover:text-red-700 font-medium">
              Sign Out
            </button>
          </div>
        </div>
      </div>

      <div className="max-w-5xl mx-auto px-5 py-6">
        <h1 className="text-2xl font-bold text-gray-900 mb-5">Profile</h1>

        {err && (
          <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-2.5 rounded-lg mb-4 text-sm">
            {err}
          </div>
        )}
        {msg && (
          <div className="bg-green-50 border border-green-200 text-green-700 px-4 py-2.5 rounded-lg mb-4 text-sm">
            {msg}
          </div>
        )}

        <div className="grid md:grid-cols-2 gap-5">
          {/* Left: Profile Picture */}
          <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-5">
            <h2 className="font-semibold text-gray-800 text-base mb-3">Profile Picture</h2>
            <div className="flex items-center gap-5">
              {picUrl ? (
                <img src={picUrl} alt="Profile" className="w-20 h-20 rounded-full object-cover border-2 border-teal-200" />
              ) : (
                <div className="w-20 h-20 rounded-full bg-teal-100 flex items-center justify-center">
                  <svg className="w-10 h-10 text-teal-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
                  </svg>
                </div>
              )}
              <div>
                <label className="cursor-pointer bg-teal-500 text-white px-3 py-1.5 rounded-lg text-sm font-medium hover:bg-teal-600 transition inline-block">
                  {uploading ? 'Uploading...' : 'Upload'}
                  <input type="file" accept="image/jpeg,image/png,image/gif" onChange={handlePicUpload} className="hidden" disabled={uploading} />
                </label>
                <p className="text-xs text-gray-400 mt-1">JPG, PNG, GIF</p>
              </div>
            </div>
            <div className="mt-4 pt-4 border-t border-gray-100 text-sm space-y-1">
              <p><span className="text-gray-500">Role:</span> <span className="text-gray-800 capitalize">{profile?.role}</span></p>
              <p><span className="text-gray-500">Status:</span> <span className={profile?.is_verified ? 'text-green-600' : 'text-amber-600'}>{profile?.is_verified ? 'Verified' : 'Unverified'}</span></p>
            </div>
          </div>

          {/* Right: Edit Profile */}
          <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-5">
            <h2 className="font-semibold text-gray-800 text-base mb-3">Edit Profile</h2>
            <form onSubmit={handleUpdateProfile}>
              <div className="mb-3">
                <label className="text-sm text-gray-600 block mb-1">Full Name</label>
                <input
                  type="text"
                  value={fullName}
                  onChange={(e) => setFullName(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-teal-500 focus:border-transparent"
                  required
                />
              </div>
              <div className="mb-3">
                <label className="text-sm text-gray-600 block mb-1">Email</label>
                <input
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-teal-500 focus:border-transparent"
                  required
                />
                <p className="text-xs text-amber-600 mt-1">Changing email may require re-verification</p>
              </div>
              <button disabled={saving} type="submit" className="bg-teal-500 text-white px-4 py-1.5 rounded-lg text-sm font-medium hover:bg-teal-600 transition disabled:opacity-50">
                {saving ? 'Saving...' : 'Save Changes'}
              </button>
            </form>
          </div>
        </div>

        {/* Change Password - Full Width */}
        <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-5 mt-5">
          <h2 className="font-semibold text-gray-800 text-base mb-3">Change Password</h2>
          <form onSubmit={handleChangePassword} className="max-w-md">
            <div className="mb-3">
              <label className="text-sm text-gray-600 block mb-1">Current Password</label>
              <input
                type="password"
                value={oldPw}
                onChange={(e) => setOldPw(e.target.value)}
                className="w-full px-3 py-2 border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-teal-500"
                required
              />
            </div>
            <div className="mb-3">
              <label className="text-sm text-gray-600 block mb-1">New Password</label>
              <div className="relative">
                <input
                  type={showPw ? 'text' : 'password'}
                  value={newPw}
                  onChange={(e) => setNewPw(e.target.value)}
                  className="w-full px-3 py-2 pr-10 border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-teal-500"
                  required
                />
                <button type="button" onClick={() => setShowPw(!showPw)} className="absolute right-3 top-2 text-gray-400">
                  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
                  </svg>
                </button>
              </div>
              {newPw && (
                <div className="mt-2">
                  <div className="h-1 bg-gray-100 rounded overflow-hidden">
                    <div className="h-full transition-all" style={{ width: `${pwVal.strength.percent}%`, backgroundColor: pwVal.strength.color }} />
                  </div>
                  <div className="flex flex-wrap gap-2 mt-1">
                    {[
                      { label: '8-20 chars', valid: pwVal.rules.len },
                      { label: 'Upper', valid: pwVal.rules.hasUpper },
                      { label: 'Lower', valid: pwVal.rules.hasLower },
                      { label: 'Number', valid: pwVal.rules.hasNumber },
                      { label: 'Special', valid: pwVal.rules.hasSpecial }
                    ].map((rule, idx) => (
                      <span key={idx} className={`text-[10px] ${rule.valid ? 'text-teal-600' : 'text-gray-400'}`}>
                        {rule.valid ? '✓' : '○'} {rule.label}
                      </span>
                    ))}
                  </div>
                </div>
              )}
            </div>
            <div className="mb-3">
              <label className="text-sm text-gray-600 block mb-1">Confirm Password</label>
              <input
                type="password"
                value={confirmPw}
                onChange={(e) => setConfirmPw(e.target.value)}
                className="w-full px-3 py-2 border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-teal-500"
                required
              />
              {confirmPw && newPw !== confirmPw && (
                <p className="text-xs text-red-500 mt-1">Passwords do not match</p>
              )}
            </div>
            <button
              disabled={pwSaving || !pwVal.isValid || newPw !== confirmPw}
              type="submit"
              className="bg-teal-500 text-white px-4 py-1.5 rounded-lg text-sm font-medium hover:bg-teal-600 transition disabled:opacity-50"
            >
              {pwSaving ? 'Updating...' : 'Update Password'}
            </button>
          </form>
        </div>
      </div>
    </div>
  );
}

export default Profile;