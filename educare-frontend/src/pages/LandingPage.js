import React from 'react';
import { Link } from 'react-router-dom';
import { FaGraduationCap, FaChalkboardTeacher, FaUsers, FaShieldAlt, FaBookOpen, FaChartLine, FaRocket, FaBrain, FaCheckCircle } from 'react-icons/fa';

function LandingPage() {
  const roles = [
    {
      id: 'student',
      title: 'Student',
      description: 'Take quizzes, track progress, and improve your math skills',
      icon: <FaGraduationCap className="w-8 h-8" />,
      link: '/student/login',
      color: 'bg-[#2563eb]',
      hoverColor: 'hover:bg-[#1d4ed8]',
      ringColor: 'ring-blue-200',
      textColor: 'text-[#2563eb]',
      bgLight: 'bg-blue-50',
      borderColor: 'hover:border-blue-300',
      btnText: 'Sign in as Student',
    },
    {
      id: 'teacher',
      title: 'Teacher',
      description: 'Create quizzes, monitor student performance, and approve materials',
      icon: <FaChalkboardTeacher className="w-8 h-8" />,
      link: '/teacher/login',
      color: 'bg-[#10b981]',
      hoverColor: 'hover:bg-[#059669]',
      ringColor: 'ring-emerald-200',
      textColor: 'text-[#10b981]',
      bgLight: 'bg-emerald-50',
      borderColor: 'hover:border-emerald-300',
      btnText: 'Sign in as Teacher',
    },
    {
      id: 'family',
      title: 'Family',
      description: "Monitor your child's progress and view reports",
      icon: <FaUsers className="w-8 h-8" />,
      link: '/family/login',
      color: 'bg-[#8b5cf6]',
      hoverColor: 'hover:bg-[#7c3aed]',
      ringColor: 'ring-violet-200',
      textColor: 'text-[#8b5cf6]',
      bgLight: 'bg-violet-50',
      borderColor: 'hover:border-violet-300',
      btnText: 'Sign in as Family',
    },
    {
      id: 'admin',
      title: 'Administrator',
      description: 'Manage users, view system stats, and configure settings',
      icon: <FaShieldAlt className="w-8 h-8" />,
      link: '/admin/login',
      color: 'bg-[#6b7280]',
      hoverColor: 'hover:bg-[#4b5563]',
      ringColor: 'ring-gray-200',
      textColor: 'text-[#6b7280]',
      bgLight: 'bg-gray-50',
      borderColor: 'hover:border-gray-300',
      btnText: 'Sign in as Admin',
    },
  ];

  const features = [
    {
      icon: <FaBookOpen className="w-6 h-6" />,
      title: 'Interactive Quizzes',
      description: 'Engaging quizzes with instant feedback to reinforce learning and track progress.',
      color: 'text-[#2563eb]',
      bg: 'bg-blue-50',
    },
    {
      icon: <FaChartLine className="w-6 h-6" />,
      title: 'Progress Tracking',
      description: 'Comprehensive analytics to monitor performance and identify areas for improvement.',
      color: 'text-[#10b981]',
      bg: 'bg-emerald-50',
    },
    {
      icon: <FaBrain className="w-6 h-6" />,
      title: 'AI-Powered Support',
      description: 'Intelligent tutoring system that adapts to each student\'s learning pace and style.',
      color: 'text-[#8b5cf6]',
      bg: 'bg-violet-50',
    },
  ];

  return (
    <div className="min-h-screen bg-[#f3f4f6]">
      {/* Header */}
      <header className="bg-white/80 backdrop-blur-md border-b border-gray-100 sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 bg-gradient-to-br from-[#2563eb] to-[#1d4ed8] rounded-xl flex items-center justify-center shadow-md shadow-blue-200">
                <FaBookOpen className="w-5 h-5 text-white" />
              </div>
              <div>
                <h1 className="text-xl font-extrabold text-gray-900 tracking-tight">EDUCARE</h1>
              </div>
            </div>
            <a
              href="#roles"
              className="hidden sm:inline-flex items-center gap-2 bg-[#2563eb] text-white px-5 py-2.5 rounded-xl text-sm font-semibold hover:bg-[#1d4ed8] transition-all shadow-md shadow-blue-200 hover:shadow-lg hover:shadow-blue-300"
            >
              <FaRocket className="w-4 h-4" />
              Get Started
            </a>
          </div>
        </div>
      </header>

      {/* Hero Section */}
      <section className="relative overflow-hidden">
        <div className="absolute inset-0 bg-gradient-to-br from-blue-50 via-white to-violet-50" />
        <div className="absolute top-20 left-10 w-72 h-72 bg-blue-200 rounded-full mix-blend-multiply filter blur-3xl opacity-30 animate-pulse" />
        <div className="absolute top-40 right-10 w-72 h-72 bg-violet-200 rounded-full mix-blend-multiply filter blur-3xl opacity-30 animate-pulse" style={{ animationDelay: '1s' }} />
        <div className="absolute bottom-10 left-1/3 w-72 h-72 bg-emerald-200 rounded-full mix-blend-multiply filter blur-3xl opacity-20 animate-pulse" style={{ animationDelay: '2s' }} />

        <div className="relative max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-20 md:py-28">
          <div className="text-center max-w-4xl mx-auto">
            <div className="inline-flex items-center gap-2 bg-white border border-blue-100 text-[#2563eb] px-4 py-2 rounded-full text-sm font-medium mb-8 shadow-sm">
              <FaRocket className="w-3.5 h-3.5" />
              AI-Powered Learning Platform
            </div>
            <h2 className="text-4xl md:text-5xl lg:text-6xl font-extrabold text-gray-900 mb-6 leading-tight tracking-tight">
              AI-Powered Mathematics
              <br />
              <span className="bg-gradient-to-r from-[#2563eb] to-[#8b5cf6] bg-clip-text text-transparent">
                Learning Support
              </span>
            </h2>
            <p className="text-lg md:text-xl text-gray-500 max-w-2xl mx-auto mb-10 leading-relaxed">
              For Ethiopian Secondary Students. Empowering learners, teachers, and families with comprehensive tools for academic excellence.
            </p>
            <div className="flex flex-col sm:flex-row items-center justify-center gap-4">
              <a
                href="#roles"
                className="w-full sm:w-auto inline-flex items-center justify-center gap-2 bg-[#2563eb] text-white px-8 py-4 rounded-xl font-semibold hover:bg-[#1d4ed8] transition-all shadow-lg shadow-blue-200 hover:shadow-xl hover:shadow-blue-300 hover:-translate-y-0.5"
              >
                Get Started
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 8l4 4m0 0l-4 4m4-4H3" />
                </svg>
              </a>
              <a
                href="#features"
                className="w-full sm:w-auto inline-flex items-center justify-center gap-2 bg-white text-gray-700 px-8 py-4 rounded-xl font-semibold hover:bg-gray-50 transition-all border border-gray-200 hover:border-gray-300 shadow-sm"
              >
                Learn More
              </a>
            </div>
          </div>
        </div>
      </section>

      {/* Role Selection Section */}
      <section id="roles" className="py-20 px-4 sm:px-6 lg:px-8">
        <div className="max-w-7xl mx-auto">
          <div className="text-center mb-14">
            <div className="inline-flex items-center gap-2 bg-white border border-gray-200 text-gray-600 px-4 py-2 rounded-full text-sm font-medium mb-6 shadow-sm">
              Choose Your Portal
            </div>
            <h3 className="text-3xl md:text-4xl font-extrabold text-gray-900 mb-4 tracking-tight">
              Select Your Role
            </h3>
            <p className="text-gray-500 max-w-2xl mx-auto text-lg">
              Choose your role to access the portal designed specifically for you.
            </p>
          </div>

          <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-6">
            {roles.map((role) => (
              <Link
                key={role.id}
                to={role.link}
                className={`group relative bg-white rounded-2xl shadow-sm hover:shadow-xl transition-all duration-300 overflow-hidden border border-gray-100 ${role.borderColor} hover:-translate-y-1 flex flex-col`}
              >
                <div className="p-7 flex flex-col flex-1">
                  <div
                    className={`${role.bgLight} w-16 h-16 rounded-2xl flex items-center justify-center ${role.textColor} mb-6 ring-4 ${role.ringColor} transition-transform group-hover:scale-110`}
                  >
                    {role.icon}
                  </div>
                  <h4 className="text-xl font-bold text-gray-900 mb-2">{role.title}</h4>
                  <p className="text-gray-500 text-sm leading-relaxed mb-6 flex-1">
                    {role.description}
                  </p>
                  <div
                    className={`${role.color} ${role.hoverColor} w-full text-white text-center py-3 rounded-xl font-semibold text-sm transition-all shadow-sm hover:shadow-md`}
                  >
                    {role.btnText}
                  </div>
                </div>
              </Link>
            ))}
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section id="features" className="py-20 px-4 sm:px-6 lg:px-8 bg-white">
        <div className="max-w-7xl mx-auto">
          <div className="text-center mb-14">
            <div className="inline-flex items-center gap-2 bg-gray-50 border border-gray-200 text-gray-600 px-4 py-2 rounded-full text-sm font-medium mb-6 shadow-sm">
              Why EDUCARE
            </div>
            <h3 className="text-3xl md:text-4xl font-extrabold text-gray-900 mb-4 tracking-tight">
              Platform Features
            </h3>
            <p className="text-gray-500 max-w-2xl mx-auto text-lg">
              Comprehensive tools designed to enhance mathematics learning and teaching.
            </p>
          </div>

          <div className="grid md:grid-cols-3 gap-8">
            {features.map((feature, index) => (
              <div
                key={index}
                className="bg-[#f3f4f6] p-8 rounded-2xl hover:shadow-lg transition-all duration-300 hover:-translate-y-1"
              >
                <div
                  className={`${feature.bg} w-14 h-14 rounded-2xl flex items-center justify-center ${feature.color} mb-6`}
                >
                  {feature.icon}
                </div>
                <h4 className="text-xl font-bold text-gray-900 mb-3">{feature.title}</h4>
                <p className="text-gray-500 leading-relaxed">{feature.description}</p>
              </div>
            ))}
          </div>

          {/* Stats */}
          <div className="mt-16 bg-gradient-to-r from-[#2563eb] to-[#1d4ed8] rounded-3xl p-10 md:p-14 shadow-xl shadow-blue-200">
            <div className="grid grid-cols-2 md:grid-cols-4 gap-8 text-center text-white">
              <div>
                <div className="text-3xl md:text-4xl font-extrabold mb-1">1000+</div>
                <div className="text-blue-200 text-sm font-medium">Active Students</div>
              </div>
              <div>
                <div className="text-3xl md:text-4xl font-extrabold mb-1">50+</div>
                <div className="text-blue-200 text-sm font-medium">Expert Teachers</div>
              </div>
              <div>
                <div className="text-3xl md:text-4xl font-extrabold mb-1">500+</div>
                <div className="text-blue-200 text-sm font-medium">Quiz Questions</div>
              </div>
              <div>
                <div className="text-3xl md:text-4xl font-extrabold mb-1">95%</div>
                <div className="text-blue-200 text-sm font-medium">Satisfaction Rate</div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Benefits Section */}
      <section className="py-20 px-4 sm:px-6 lg:px-8 bg-[#f3f4f6]">
        <div className="max-w-7xl mx-auto">
          <div className="grid md:grid-cols-2 gap-12 items-center">
            <div>
              <div className="inline-flex items-center gap-2 bg-white border border-gray-200 text-gray-600 px-4 py-2 rounded-full text-sm font-medium mb-6 shadow-sm">
                Built for Ethiopia
              </div>
              <h3 className="text-3xl md:text-4xl font-extrabold text-gray-900 mb-6 tracking-tight">
                Designed for Your Success
              </h3>
              <p className="text-gray-500 text-lg mb-8 leading-relaxed">
                EDUCARE is tailored specifically for Ethiopian secondary school students, aligning with the national mathematics curriculum to ensure relevant and effective learning.
              </p>
              <ul className="space-y-4">
                {[
                  'Curriculum-aligned quiz content',
                  'Real-time progress tracking',
                  'Parent and teacher collaboration',
                  'AI-powered personalized learning paths',
                ].map((item, i) => (
                  <li key={i} className="flex items-center gap-3">
                    <div className="w-6 h-6 bg-emerald-100 rounded-full flex items-center justify-center flex-shrink-0">
                      <FaCheckCircle className="w-4 h-4 text-[#10b981]" />
                    </div>
                    <span className="text-gray-700 font-medium">{item}</span>
                  </li>
                ))}
              </ul>
            </div>
            <div className="bg-white rounded-3xl p-10 shadow-lg border border-gray-100">
              <div className="grid grid-cols-2 gap-6">
                {[
                  { icon: <FaGraduationCap className="w-8 h-8" />, label: 'Students', color: 'text-[#2563eb]', bg: 'bg-blue-50' },
                  { icon: <FaChalkboardTeacher className="w-8 h-8" />, label: 'Teachers', color: 'text-[#10b981]', bg: 'bg-emerald-50' },
                  { icon: <FaUsers className="w-8 h-8" />, label: 'Families', color: 'text-[#8b5cf6]', bg: 'bg-violet-50' },
                  { icon: <FaShieldAlt className="w-8 h-8" />, label: 'Admins', color: 'text-[#6b7280]', bg: 'bg-gray-100' },
                ].map((item, i) => (
                  <div key={i} className="text-center p-6 rounded-2xl bg-[#f3f4f6] hover:shadow-md transition-all">
                    <div className={`${item.bg} w-16 h-16 rounded-2xl flex items-center justify-center ${item.color} mx-auto mb-3`}>
                      {item.icon}
                    </div>
                    <div className="font-semibold text-gray-900">{item.label}</div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="bg-gray-900 text-white py-14 px-4 sm:px-6 lg:px-8">
        <div className="max-w-7xl mx-auto">
          <div className="grid md:grid-cols-4 gap-10">
            <div className="md:col-span-2">
              <div className="flex items-center gap-3 mb-5">
                <div className="w-10 h-10 bg-gradient-to-br from-[#2563eb] to-[#1d4ed8] rounded-xl flex items-center justify-center shadow-lg">
                  <FaBookOpen className="w-5 h-5 text-white" />
                </div>
                <span className="text-xl font-extrabold tracking-tight">EDUCARE</span>
              </div>
              <p className="text-gray-400 leading-relaxed max-w-sm">
                AI-powered mathematics learning support for Ethiopian secondary students. Empowering education through technology and innovation.
              </p>
            </div>

            <div>
              <h5 className="font-semibold mb-5 text-gray-300 uppercase text-xs tracking-wider">Quick Links</h5>
              <ul className="space-y-3">
                <li><a href="#roles" className="text-gray-400 hover:text-white transition text-sm">Get Started</a></li>
                <li><a href="#features" className="text-gray-400 hover:text-white transition text-sm">Features</a></li>
              </ul>
            </div>

            <div>
              <h5 className="font-semibold mb-5 text-gray-300 uppercase text-xs tracking-wider">Portals</h5>
              <ul className="space-y-3">
                <li><Link to="/student/login" className="text-gray-400 hover:text-white transition text-sm">Student Login</Link></li>
                <li><Link to="/teacher/login" className="text-gray-400 hover:text-white transition text-sm">Teacher Login</Link></li>
                <li><Link to="/family/login" className="text-gray-400 hover:text-white transition text-sm">Family Login</Link></li>
                <li><Link to="/admin/login" className="text-gray-400 hover:text-white transition text-sm">Admin Login</Link></li>
              </ul>
            </div>
          </div>

          <div className="border-t border-gray-800 mt-10 pt-8 flex flex-col sm:flex-row items-center justify-between gap-4">
            <p className="text-gray-500 text-sm">
              &copy; {new Date().getFullYear()} EDUCARE. All rights reserved.
            </p>
            <p className="text-gray-500 text-sm">
              Built for Ethiopian Secondary Students
            </p>
          </div>
        </div>
      </footer>
    </div>
  );
}

export default LandingPage;
