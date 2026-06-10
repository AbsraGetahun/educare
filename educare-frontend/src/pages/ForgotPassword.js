import React, { useState, useMemo } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { forgotPassword, resetPassword } from '../services/api';
import { validatePassword } from '../utils/passwordRules';

function ForgotPassword() {
  const [step, setStep] = useState(1); // 1: request email, 2: enter OTP + new pw
  const [email, setEmail] = useState('');
  const [otp, setOtp] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [showPw, setShowPw] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();

  const pwValidation = useMemo(() => validatePassword(newPassword), [newPassword]);
  const passwordsMatch = confirmPassword === newPassword && confirmPassword.length > 0;

  const handleRequestOtp = async (e) => {
    e.preventDefault();
    setError(''); setSuccess(''); setLoading(true);
    try {
      await forgotPassword(email);
      setSuccess('OTP sent! Check your email (valid 10 minutes).');
      setStep(2);
    } catch (err) {
      setError(err.response?.data?.error || 'Failed to send OTP');
    } finally {
      setLoading(false);
    }
  };

  const handleReset = async (e) => {
    e.preventDefault();
    setError(''); setSuccess('');
    if (!otp || otp.length !== 6) {
      setError('Please enter the 6-digit OTP');
      return;
    }
    if (newPassword !== confirmPassword) {
      setError('Passwords do not match');
      return;
    }
    if (!pwValidation.isValid) {
      setError('New password does not meet strength requirements');
      return;
    }
    setLoading(true);
    try {
      await resetPassword(email, otp, newPassword);
      setSuccess('Password reset successful! Redirecting to login...');
      setTimeout(() => navigate('/student/login', { state: { message: 'Password reset. Please log in.' } }), 1600);
    } catch (err) {
      const resp = err.response?.data;
      setError(resp?.error || 'Reset failed. Check OTP and try again.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 to-teal-50 flex items-center justify-center p-4">
      <div className="w-full max-w-md">
        <div className="text-center mb-8">
          <Link to="/" className="inline-flex items-center justify-center mb-6">
            <div className="w-12 h-12 bg-teal-500 rounded-xl flex items-center justify-center shadow-md">
              <svg className="w-7 h-7 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" /></svg>
            </div>
          </Link>
          <h1 className="text-3xl font-bold text-gray-900 mb-2">Forgot Password</h1>
          <p className="text-gray-600">EDUCARE • Reset via 6-digit OTP</p>
        </div>

        <div className="bg-white rounded-2xl shadow-xl p-8">
          {error && <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg mb-4 text-sm">{error}</div>}
          {success && <div className="bg-green-50 border border-green-200 text-green-700 px-4 py-3 rounded-lg mb-4 text-sm">{success}</div>}

          {step === 1 && (
            <form onSubmit={handleRequestOtp}>
              <div className="mb-6">
                <label className="block text-gray-700 text-sm font-semibold mb-2">Email Address</label>
                <input
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-teal-500 focus:border-transparent transition"
                  placeholder="your@email.com"
                  required
                />
              </div>
              <button
                type="submit"
                disabled={loading}
                className="w-full bg-teal-500 text-white py-3 rounded-lg font-semibold hover:bg-teal-600 transition disabled:opacity-50"
              >
                {loading ? 'Sending OTP...' : 'Send 6-Digit OTP'}
              </button>
            </form>
          )}

          {step === 2 && (
            <form onSubmit={handleReset}>
              <div className="mb-4 text-sm text-gray-600">
                OTP sent to <span className="font-medium">{email}</span>. Enter it below (expires in 10 min, 3 attempts max).
              </div>

              <div className="mb-6">
                <label className="block text-gray-700 text-sm font-semibold mb-2">6-Digit OTP</label>
                <input
                  type="text"
                  value={otp}
                  onChange={(e) => setOtp(e.target.value.replace(/\D/g, '').slice(0,6))}
                  className="w-full px-4 py-3 border border-gray-300 rounded-lg tracking-[8px] text-center text-xl font-mono focus:outline-none focus:ring-2 focus:ring-teal-500 focus:border-transparent transition"
                  placeholder="123456"
                  maxLength={6}
                  required
                />
              </div>

              <div className="mb-4">
                <label className="block text-gray-700 text-sm font-semibold mb-2">New Password</label>
                <div className="relative">
                  <input
                    type={showPw ? 'text' : 'password'}
                    value={newPassword}
                    onChange={(e) => setNewPassword(e.target.value)}
                    className="w-full px-4 py-3 pr-12 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-teal-500 focus:border-transparent transition font-mono"
                    placeholder="New strong password"
                    required
                  />
                  <button type="button" onClick={() => setShowPw(!showPw)} className="absolute right-3 top-3 text-gray-500">
                    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
                    </svg>
                  </button>
                </div>

                {newPassword && (
                  <>
                    <div className="mt-2 h-1.5 bg-gray-200 rounded overflow-hidden">
                      <div className="h-full transition-all" style={{width: `${pwValidation.strength.percent}%`, backgroundColor: pwValidation.strength.color}} />
                    </div>
                    <div className="text-xs mt-1" style={{color: pwValidation.strength.color}}>{pwValidation.strength.label}</div>
                  </>
                )}

                {newPassword && (
                  <div className="mt-2 text-xs bg-gray-50 p-2 rounded border">
                    {['8-20 chars','Upper','Lower','Number','Special (!@#$%^&*)'].map((l,i) => {
                      const ok = Object.values(pwValidation.rules)[i];
                      return <div key={i} className={ok ? 'text-teal-600' : 'text-gray-500'}>• {l} {ok ? '✓' : ''}</div>;
                    })}
                  </div>
                )}
              </div>

              <div className="mb-6">
                <label className="block text-gray-700 text-sm font-semibold mb-2">Confirm New Password</label>
                <input
                  type="password"
                  value={confirmPassword}
                  onChange={(e) => setConfirmPassword(e.target.value)}
                  className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-teal-500 focus:border-transparent transition"
                  required
                />
                {confirmPassword && !passwordsMatch && <p className="text-red-500 text-xs mt-1">Passwords do not match</p>}
              </div>

              <button
                type="submit"
                disabled={loading || !pwValidation.isValid || !passwordsMatch}
                className="w-full bg-teal-500 text-white py-3 rounded-lg font-semibold hover:bg-teal-600 transition disabled:opacity-50"
              >
                {loading ? 'Resetting...' : 'Reset Password'}
              </button>

              <button type="button" onClick={() => { setStep(1); setOtp(''); setNewPassword(''); }} className="mt-3 w-full text-sm text-gray-500 hover:text-gray-700">
                ← Request new OTP
              </button>
            </form>
          )}

          <div className="mt-6 text-center">
            <Link to="/student/login" className="text-teal-600 hover:text-teal-700 text-sm font-medium">
              Back to Login
            </Link>
          </div>
        </div>
      </div>
    </div>
  );
}

export default ForgotPassword;