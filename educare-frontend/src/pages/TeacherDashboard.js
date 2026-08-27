import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { getQuizzes, getStudents, getStudentGaps, getQuizResults, getQuizById, createQuiz, updateQuiz, deleteQuiz, getPendingMaterials, approveMaterial, rejectMaterial, getTeacherMasteryOverview, getHeatmap, searchCurriculum, generatePracticeMaterial, generateMaterialByTopic, searchCurriculumByTopic, generateAIQuiz, getMaterialsAnalytics, getCurriculumTopics, generateBatchMaterials } from '../services/api';
import FilePicker from '../components/FilePicker';
import MathContent from '../components/MathContent';
import { resolveUploadUrl } from '../utils/uploadUrl';
import { OverviewTab, MasteryTab, CurriculumTab, HeatmapTab, StudentsTab, QuizzesTab, ApprovalsTab } from '../components/TeacherTabPanels';

function TeacherDashboard() {
  const [activeTab, setActiveTab] = useState('overview');
  const [quizzes, setQuizzes] = useState([]);
  const [students, setStudents] = useState([]);
  const [selectedStudent, setSelectedStudent] = useState(null);
  const [studentGaps, setStudentGaps] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [showCreateQuiz, setShowCreateQuiz] = useState(false);
  const [showEditQuiz, setShowEditQuiz] = useState(false);
  const [editingQuiz, setEditingQuiz] = useState(null);
  const [selectedQuizResults, setSelectedQuizResults] = useState(null);
  const [showResultsModal, setShowResultsModal] = useState(false);
  const [pendingMaterials, setPendingMaterials] = useState([]);
  const [showRejectConfirm, setShowRejectConfirm] = useState(null);
  const [masteryOverview, setMasteryOverview] = useState([]);
  const [totalStudents, setTotalStudents] = useState(0);
  const [expandedTopic, setExpandedTopic] = useState(null);
  const [heatmapData, setHeatmapData] = useState([]);
  const [selectedHeatmapTopic, setSelectedHeatmapTopic] = useState(null);
  const [curriculumQuery, setCurriculumQuery] = useState('');
  const [curriculumResults, setCurriculumResults] = useState([]);
  const [curriculumLoading, setCurriculumLoading] = useState(false);
  const [curriculumSearched, setCurriculumSearched] = useState(false);
  const [curriculumGeneratingIds, setCurriculumGeneratingIds] = useState({});
  const [batchGenProgress, setBatchGenProgress] = useState(null);
  const [batchGenSummary, setBatchGenSummary] = useState(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [generateTopic, setGenerateTopic] = useState('');
  const [generateDifficulty, setGenerateDifficulty] = useState('medium');
  const [generateStatus, setGenerateStatus] = useState('');
  const [isGenerating, setIsGenerating] = useState(false);
  const [showTopicGeneratorModal, setShowTopicGeneratorModal] = useState(false);
  const [topicInput, setTopicInput] = useState('');
  const [topicGenPreview, setTopicGenPreview] = useState('');
  const [topicGenStatus, setTopicGenStatus] = useState('');
  const [topicGenLoading, setTopicGenLoading] = useState(false);
  const [topicGenStep, setTopicGenStep] = useState(1);
  const [topicGenStudentId, setTopicGenStudentId] = useState('');
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
    time_limit: '30',
    questions: []
  });
  const [newQuestion, setNewQuestion] = useState({
    question_text: '',
    option_a: '',
    option_b: '',
    option_c: '',
    option_d: '',
    correct_answer: 'A',
    question_image: '',
  });
  const [newQuestionImageFile, setNewQuestionImageFile] = useState([]);
  const [showAIQuizModal, setShowAIQuizModal] = useState(false);
  const [aiQuizTopic, setAiQuizTopic] = useState('');
  const [aiQuizNumQ, setAiQuizNumQ] = useState(5);
  const [aiQuizDiff, setAiQuizDiff] = useState('medium');
  const [aiQuizSuggestions, setAiQuizSuggestions] = useState([]);
  const [aiQuizLoading, setAiQuizLoading] = useState(false);
  const [aiQuizResult, setAiQuizResult] = useState(null);
  const [aiQuizError, setAiQuizError] = useState('');
  const [topicSuggestionVisible, setTopicSuggestionVisible] = useState(false);
  const [analyticsData, setAnalyticsData] = useState(null);
  const [analyticsLoading, setAnalyticsLoading] = useState(false);
  const [batchResult, setBatchResult] = useState(null);
  const [batchLoading, setBatchLoading] = useState(false);
  
  const navigate = useNavigate();
  const fullName = localStorage.getItem('full_name');
  const teacherUserId = localStorage.getItem('user_id');
  const assignedGrade = localStorage.getItem('assigned_grade') || '';
  const assignedGradeNum = assignedGrade ? parseInt(assignedGrade, 10) : null;
  
  const [heatmapGradeFilter, setHeatmapGradeFilter] = useState(assignedGrade || 'all');
  const [heatmapSort, setHeatmapSort] = useState('mastery');
  const [topicGradeLevel, setTopicGradeLevel] = useState(assignedGrade || '10');
  const [topicDifficulty, setTopicDifficulty] = useState('medium');
  const [aiQuizGrade, setAiQuizGrade] = useState(assignedGrade || '10');
  const [batchGrade, setBatchGrade] = useState(assignedGrade || '10');
  const [batchTopic, setBatchTopic] = useState('');
  const [batchDiff, setBatchDiff] = useState('medium');
  const [topicGenForAll, setTopicGenForAll] = useState(false);

  const handleTopicInputChange = async (val, forMaterial = false) => {
    if (forMaterial) {
      setTopicInput(val);
    } else {
      setAiQuizTopic(val);
      setAiQuizError('');
    }
    if (val.trim().length >= 2) {
      try {
        const d = await getCurriculumTopics(val.trim());
        const list = d.topics || [];
        if (forMaterial) {
          setAiQuizSuggestions(list);
          setTopicSuggestionVisible(true);
        } else {
          setAiQuizSuggestions(list);
        }
      } catch {
        setAiQuizSuggestions([]);
      }
    } else {
      setAiQuizSuggestions([]);
      if (forMaterial) setTopicSuggestionVisible(false);
    }
  };

  const selectSuggestion = (s) => {
    setAiQuizTopic(s.topic);
    setAiQuizSuggestions([]);
  };

  const handleGenerateAIQuiz = async () => {
    if (!aiQuizTopic.trim()) return;
    setAiQuizLoading(true);
    setAiQuizError('');
    setAiQuizResult(null);
    try {
      const q = aiQuizTopic.toLowerCase();
      let grade = aiQuizGrade;
      if (['probability', 'statistics', 'matrix'].some(t => q.includes(t))) {
        grade = '12';
      } else if (q.includes('trig') || q.includes('geometry')) {
        grade = '11';
      }
      const data = await generateAIQuiz({
        topic:         aiQuizTopic,
        grade_level:   parseInt(grade),
        num_questions: aiQuizNumQ,
        difficulty:    aiQuizDiff,
      });
      setAiQuizResult(data);
      setShowAIQuizModal(false);
      alert(`AI Quiz generated: "${data.title}" with ${data.num_questions} questions.`);
      fetchData();
    } catch (err) {
      setAiQuizError(err.response?.data?.error || 'Failed to generate quiz');
    } finally {
      setAiQuizLoading(false);
    }
  };

  const loadAnalytics = async () => {
    setAnalyticsLoading(true);
    try {
      const data = await getMaterialsAnalytics(
        assignedGradeNum,
        teacherUserId ? parseInt(teacherUserId, 10) : undefined
      );
      setAnalyticsData(data);
    } catch (err) {
      console.error('Analytics load failed:', err);
      setAnalyticsData(null);
      alert('Failed to load analytics: ' + (err.response?.data?.error || err.message));
    } finally {
      setAnalyticsLoading(false);
    }
  };

  const handleBatchGenerate = async () => {
    if (!batchTopic.trim()) {
      alert('Enter a topic for batch generation.');
      return;
    }
    setBatchLoading(true);
    setBatchResult(null);
    try {
      const grade = assignedGradeNum || parseInt(batchGrade, 10);
      const data = await generateBatchMaterials({
        topic_name: batchTopic.trim(),
        grade_level: grade,
        difficulty: batchDiff,
        teacher_id: teacherUserId ? parseInt(teacherUserId, 10) : undefined,
      });
      setBatchResult(data);
      const materialsData = await getPendingMaterials();
      setPendingMaterials(materialsData.materials || []);
      alert(
        `${data.message}\n\n${data.generated} material(s) created for ${data.total_students} student(s). ` +
        'Approve them in Pending Approvals so students can see them.'
      );
    } catch (err) {
      alert('Batch generation failed: ' + (err.response?.data?.error || err.message));
    } finally {
      setBatchLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  useEffect(() => {
    if (assignedGradeNum) {
      setBatchGrade(String(assignedGradeNum));
      setTopicGradeLevel(String(assignedGradeNum));
    }
  }, [assignedGradeNum]);

  useEffect(() => {
    if (activeTab === 'analytics') {
      loadAnalytics();
    }
  }, [activeTab]);

  const fetchData = async () => {
    setLoading(true);
    setError('');
    if (!assignedGradeNum) {
      setError('No grade assigned to your teacher account. Contact an administrator.');
      setLoading(false);
      return;
    }
    try {
      const [quizzesData, studentsData, materialsData, masteryData, heatmapResult] = await Promise.all([
        getQuizzes(),
        getStudents(assignedGradeNum),
        getPendingMaterials(),
        getTeacherMasteryOverview(assignedGradeNum),
        getHeatmap(assignedGradeNum)
      ]);
      setQuizzes(quizzesData.quizzes || []);
      setStudents(studentsData.students || []);
      setPendingMaterials(materialsData.materials || []);
      setMasteryOverview(masteryData.overview || []);
      setTotalStudents(masteryData.total_students || 0);
      setHeatmapData(heatmapResult.heatmap || []);
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
      console.error('Failed to load gaps', err);
      setStudentGaps([]);
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
    if (!quizForm.title || !quizForm.topic_id) {
      alert('Please fill title and select a topic');
      return;
    }

    try {
      const payload = {
        title: quizForm.title,
        topic_id: parseInt(quizForm.topic_id),
        total_marks: quizForm.total_marks || quizForm.questions.length,
        time_limit: quizForm.time_limit || 30,
        questions: quizForm.questions
      };
      const result = await createQuiz(payload);
      if (result.quiz_id) {
        alert(`Quiz created successfully with ${quizForm.questions.length} questions!`);
      } else {
        alert('Quiz created but may have errors: ' + (result.error || ''));
      }
      setShowCreateQuiz(false);
      setQuizForm({ title: '', topic_id: '', total_marks: '', time_limit: '30', questions: [] });
      fetchData();
    } catch (err) {
      alert('Failed to create quiz');
    }
  };

  const handleAddQuestion = () => {
    if (!newQuestion.question_text || !newQuestion.option_a || !newQuestion.option_b) {
      alert('Please fill in question text and at least two options');
      return;
    }
    const imageUrl = newQuestionImageFile[0]?.url || newQuestion.question_image || '';
    setQuizForm({
      ...quizForm,
      questions: [...quizForm.questions, { ...newQuestion, question_image: imageUrl }],
    });
    setNewQuestion({
      question_text: '',
      option_a: '',
      option_b: '',
      option_c: '',
      option_d: '',
      correct_answer: 'A',
      question_image: '',
    });
    setNewQuestionImageFile([]);
  };

  const handleRemoveQuestion = (index) => {
    setQuizForm({
      ...quizForm,
      questions: quizForm.questions.filter((_, i) => i !== index)
    });
  };

  const handleApproveMaterial = async (materialId, studentId = null) => {
    console.log('📝 handleApproveMaterial called with:', { materialId, studentId });
    
    const material = pendingMaterials.find((m) => m.material_id === materialId);
    const hasAssignment = material?.assigned_students?.length > 0;
    
    if (!hasAssignment && !studentId) {
      alert('Please select which student this material is for, then click Approve.');
      return;
    }
    
    try {
      console.log('📤 Calling approveMaterial API with:', { materialId, studentId });
      const result = await approveMaterial(materialId, studentId);
      console.log('✅ API Response:', result);
      
      if (result.error) {
        alert(result.error);
        return;
      }
      
      setPendingMaterials(pendingMaterials.filter(m => m.material_id !== materialId));
      const names = (result.assigned_students || []).map((s) => s.full_name).join(', ');
      alert(names
        ? `Material approved and sent to: ${names}`
        : 'Material approved successfully!');
      
      const materialsData = await getPendingMaterials();
      setPendingMaterials(materialsData.materials || []);
    } catch (err) {
      console.error('❌ Error approving material:', err);
      const msg = err.response?.data?.error || 'Failed to approve material';
      alert(msg);
    }
  };

  const handleEditQuiz = async (quiz) => {
    setEditingQuiz(quiz);
    setShowEditQuiz(true);
    try {
      const full = await getQuizById(quiz.quiz_id);
      setQuizForm({
        title: full.title || quiz.title,
        topic_id: quiz.topic_id || '',
        total_marks: full.total_marks || quiz.total_marks || '',
        time_limit: full.time_limit || quiz.time_limit || '30',
        questions: full.questions || [],
      });
    } catch {
      setQuizForm({
        title: quiz.title,
        topic_id: quiz.topic_id || '',
        total_marks: quiz.total_marks || '',
        time_limit: quiz.time_limit || '30',
        questions: quiz.questions || [],
      });
    }
    setNewQuestionImageFile([]);
  };

  const handleUpdateQuiz = async () => {
    if (!editingQuiz) return;
    try {
      const payload = {
        title: quizForm.title,
        topic_id: parseInt(quizForm.topic_id),
        total_marks: quizForm.total_marks || quizForm.questions.length,
        time_limit: quizForm.time_limit || 30,
        questions: quizForm.questions
      };
      await updateQuiz(editingQuiz.quiz_id, payload);
      alert('Quiz updated successfully!');
      setShowEditQuiz(false);
      setEditingQuiz(null);
      setQuizForm({ title: '', topic_id: '', total_marks: '', time_limit: '30', questions: [] });
      fetchData();
    } catch (err) {
      alert('Failed to update quiz');
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
    navigate('/');
  };

  const handleCurriculumSearch = async (e) => {
    e.preventDefault();
    if (!curriculumQuery.trim()) return;
    setCurriculumLoading(true);
    setCurriculumSearched(true);
    try {
      const data = await searchCurriculum(curriculumQuery);
      setCurriculumResults(data.results || []);
    } catch (err) {
      setCurriculumResults([]);
    } finally {
      setCurriculumLoading(false);
    }
  };

  const handleGenerateFromSearchResult = async (result, index, difficulty = 'medium') => {
    const studentId = selectedStudent?.user_id;
    if (!studentId) {
      alert('Select a student in the Students tab first so the material is assigned to them.');
      return;
    }
    setCurriculumGeneratingIds(prev => ({ ...prev, [index]: true }));
    try {
      let topicName = '';
      if (result.section) {
        topicName = result.section.replace(/^Unit\s+\d+\s*:\s*/i, '').trim();
      }
      if (!topicName && result.text) {
        const m = result.text.match(/Unit\s+\d+\s*:\s*([^\n]+)/i);
        if (m) {
          topicName = m[1].trim();
        }
      }
      if (!topicName) {
        topicName = curriculumQuery.trim();
      }
      if (topicName.length > 50) {
        topicName = topicName.substring(0, 50);
      }

      const grade = assignedGradeNum || result.grade_level || result.source_grade || 10;
      const data = await generateMaterialByTopic(
        topicName,
        grade,
        difficulty,
        teacherUserId ? parseInt(teacherUserId, 10) : undefined,
        studentId,
        { forAllStudents: false }
      );
      
      alert(`Material successfully generated for ${selectedStudent.full_name}!\n\nTitle: ${data.title}\nGrade: ${data.grade_level}\nDifficulty: ${data.difficulty}\n\nIt is now pending approval in the "Pending Approvals" tab.`);
      
      const materialsData = await getPendingMaterials();
      setPendingMaterials(materialsData.materials || []);
      fetchData();
    } catch (err) {
      console.error(err);
      alert('Failed to generate material from this search result. Please try again.');
    } finally {
      setCurriculumGeneratingIds(prev => ({ ...prev, [index]: false }));
    }
  };

  const handleGenerateBatchForStruggling = async (difficulty = 'medium') => {
    const seen = new Set();
    const weakItems = [];
    masteryOverview.forEach(topic => {
      if (topic.struggling_students && topic.struggling_students.length > 0) {
        topic.struggling_students.forEach(student => {
          const key = `${student.student_id}_${topic.topic_id}`;
          if (!seen.has(key)) {
            seen.add(key);
            weakItems.push({
              studentId: student.student_id,
              studentName: student.full_name,
              topicName: topic.topic_name,
              topicId: topic.topic_id,
              gradeLevel: topic.grade_level,
              avgScore: student.avg_score
            });
          }
        });
      }
    });

    if (weakItems.length === 0) {
      alert("No struggling students with weak topics (average score < 70%) were found in the current tracker!");
      return;
    }

    setBatchGenSummary(null);
    setBatchGenProgress({
      current: 0,
      total: weakItems.length,
      currentStudent: '',
      currentTopic: ''
    });

    const generated = [];
    const failed = [];

    for (let i = 0; i < weakItems.length; i++) {
      const item = weakItems[i];
      setBatchGenProgress({
        current: i + 1,
        total: weakItems.length,
        currentStudent: item.studentName,
        currentTopic: item.topicName
      });

      try {
        const res = await generatePracticeMaterial(
          item.topicName, item.studentId, difficulty, true, teacherUserId, assignedGradeNum
        );
        generated.push({
          studentName: item.studentName,
          topicName: item.topicName,
          title: res.title || `Practice: ${item.topicName}`,
          status: 'success'
        });
      } catch (err) {
        console.error(`Failed to generate for ${item.studentName} on ${item.topicName}:`, err);
        const isDuplicate = err.response && err.response.status === 409;
        failed.push({
          studentName: item.studentName,
          topicName: item.topicName,
          error: isDuplicate ? "Already generated within last 7 days" : (err.response?.data?.error || "Generation error"),
          status: isDuplicate ? 'duplicate' : 'failed'
        });
      }
    }

    setBatchGenProgress(null);
    setBatchGenSummary({
      generated,
      failed
    });

    const materialsData = await getPendingMaterials();
    setPendingMaterials(materialsData.materials || []);
    fetchData();
  };

  const handleSearch = async () => {
    if (!searchQuery.trim()) return;
    setIsLoading(true);
    try {
      const data = await searchCurriculum(searchQuery);
      setSearchResults(data.results || []);
    } catch (err) {
      setSearchResults([]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleGenerateMaterial = async () => {
    if (!generateTopic || !selectedStudent) return;
    setIsGenerating(true);
    setGenerateStatus('');
    try {
      const res = await generatePracticeMaterial(
        generateTopic, selectedStudent.user_id, generateDifficulty, false, teacherUserId, assignedGradeNum
      );
      if (res.duplicate) {
        alert(res.message || 'Existing pending material linked to this student — you can approve it now.');
      }
      setGenerateStatus('success');
      const materialsData = await getPendingMaterials();
      setPendingMaterials(materialsData.materials || []);
      fetchData();
    } catch (err) {
      setGenerateStatus('error');
      const msg = err.response?.data?.error || 'Generation failed';
      alert(err.response?.status === 409
        ? `${msg}\n\nOpen Pending Approvals — an existing material may already be waiting.`
        : msg);
    } finally {
      setIsGenerating(false);
    }
  };

  const handleGenerateForWeakness = async (gap) => {
    if (!selectedStudent) return;
    setGenerateTopic(gap.topic_name);
    setIsGenerating(true);
    setGenerateStatus('');
    try {
      const res = await generatePracticeMaterial(
        gap.topic_name, selectedStudent.user_id, generateDifficulty, false, teacherUserId, assignedGradeNum
      );
      setGenerateStatus('success');
      const materialsData = await getPendingMaterials();
      setPendingMaterials(materialsData.materials || []);
      alert(res.duplicate
        ? (res.message || `Existing pending material for "${gap.topic_name}" is ready to approve.`)
        : `Material generated for "${gap.topic_name}" — pending approval.`);
    } catch (err) {
      const msg = err.response?.data?.error || 'Generation failed';
      setGenerateStatus('error');
      alert(err.response?.status === 409
        ? `${msg}\n\nCheck Pending Approvals for an existing material.`
        : msg);
    } finally {
      setIsGenerating(false);
    }
  };

  const handleDeleteQuiz = async (quizId) => {
    if (!window.confirm('Delete this quiz?')) return;
    try {
      await deleteQuiz(quizId);
      fetchData();
    } catch {
      alert('Failed to delete quiz');
    }
  };

  const handleOpenTopicGenerator = () => {
    setShowTopicGeneratorModal(true);
    setTopicGenStep(1);
    setTopicInput('');
    setTopicGradeLevel(assignedGrade || '10');
    setTopicDifficulty('medium');
    setTopicGenPreview('');
    setTopicGenStatus('');
    setTopicGenStudentId(selectedStudent?.user_id ? String(selectedStudent.user_id) : '');
  };

  const handleCloseTopicGenerator = () => {
    setShowTopicGeneratorModal(false);
  };

  const handleSearchCurriculumPreview = async () => {
    if (!topicInput.trim()) return;
    setTopicGenLoading(true);
    setTopicGenStatus('');
    setTopicGenPreview('');
    setTopicGenStep(1);
    try {
      const data = await searchCurriculumByTopic(
        topicInput.trim(),
        assignedGradeNum || topicGradeLevel
      );
      const results = data.results || [];
      if (results.length === 0) {
        setTopicGenStatus('no_results');
        setTopicGenPreview('No curriculum content found for this topic. Try a different keyword.');
        setTopicGenStep(2);
      } else {
        const previewHtml = results
          .map((r, i) =>
            `<div class="mb-2 p-2 border rounded" style="border-color:#e5e7eb">
              <span class="font-semibold text-sm">Result ${i + 1}</span>
              <span class="text-[10px] px-1.5 py-0.5 rounded-full bg-emerald-100 text-emerald-700 font-medium ml-2">${r.source_file || r.source || 'curriculum'}</span>
              ${r.source_grade ? `<span class="text-[10px] px-1.5 py-0.5 rounded-full bg-purple-100 text-purple-700 font-medium ml-1">Grade ${r.source_grade}</span>` : ''}
              <span class="text-xs text-gray-500 ml-2">p.${r.source_page || r.page || '?'}</span>
              <p class="text-xs mt-1">${r.text}</p>
            </div>`
          )
          .join('');
        setTopicGenPreview(previewHtml);
        setTopicGenStatus('found');
        setTopicGenStep(2);
      }
    } catch (err) {
      setTopicGenStatus('error');
      setTopicGenPreview('Search failed. Please try again.');
      setTopicGenStep(2);
    } finally {
      setTopicGenLoading(false);
    }
  };

  const handleGenerateMaterialByTopic = async () => {
    if (!topicInput.trim()) return;
    if (!topicGenForAll && !topicGenStudentId) {
      alert('Select a student, or check "Generate for all students in my grade".');
      return;
    }
    setTopicGenLoading(true);
    setTopicGenStatus('');
    try {
      const grade = assignedGradeNum || parseInt(topicGradeLevel, 10);
      const data = await generateMaterialByTopic(
        topicInput.trim(),
        grade,
        topicDifficulty,
        teacherUserId ? parseInt(teacherUserId, 10) : undefined,
        topicGenForAll ? null : parseInt(topicGenStudentId, 10),
        { forAllStudents: topicGenForAll }
      );
      setTopicGenStatus('generated');
      const batchInfo = data.generated != null
        ? `<p class="text-xs text-gray-700"><strong>Created:</strong> ${data.generated} material(s) for ${data.total_students} students</p>`
        : `<p class="text-xs text-gray-700"><strong>Title:</strong> ${data.title || ''}</p>`;
      setTopicGenPreview(
        `<div class="p-3 rounded" style="background-color:#ecfdf5">
          <p class="text-sm font-semibold text-green-700">Material generated successfully!</p>
          ${batchInfo}
          <p class="text-xs text-gray-700"><strong>Topic:</strong> ${data.topic_name || topicInput}</p>
          <p class="text-xs text-gray-700"><strong>Grade:</strong> ${data.grade_level}</p>
          ${data.difficulty ? `<p class="text-xs text-gray-700"><strong>Difficulty:</strong> ${data.difficulty}</p>` : ''}
          ${data.questions_count ? `<p class="text-xs text-gray-700"><strong>Questions:</strong> ${data.questions_count}</p>` : ''}
          <p class="text-xs text-gray-500 mt-1">${data.message}</p>
          <p class="text-xs text-amber-700 mt-2">Approve in Pending Approvals so students can see them.</p>
        </div>`
      );
      setTopicGenStep(3);
      const materialsData = await getPendingMaterials();
      setPendingMaterials(materialsData.materials || []);
      fetchData();
    } catch (err) {
      setTopicGenStatus('error');
      setTopicGenPreview('Failed to generate material. Please try again.');
      setTopicGenStep(2);
    } finally {
      setTopicGenLoading(false);
    }
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
    <div className="min-h-screen bg-gray-100" style={{ backgroundColor: '#f3f4f6' }}>
      {/* Navigation Bar */}
      <nav className="bg-white shadow-sm sticky top-0 z-10" style={{ backgroundColor: '#ffffff' }}>
        <div className="max-w-7xl mx-auto px-4">
          <div className="flex justify-between items-center py-3">
            <div className="flex items-center gap-4">
              <h1 className="text-lg font-bold" style={{ color: '#2563eb' }}>EDUCARE</h1>
              <span className="text-gray-400">|</span>
              <span className="text-gray-600 text-sm">Teacher Portal</span>
              {assignedGradeNum && (
                <span className="text-xs font-semibold px-2 py-0.5 rounded bg-green-100 text-green-800">
                  Grade {assignedGradeNum} only
                </span>
              )}
            </div>
            <div className="flex items-center gap-4">
              <span className="text-gray-600 text-sm">Welcome, {fullName}</span>
              <button
                onClick={handleLogout}
                className="px-3 py-1.5 text-sm rounded-md transition"
                style={{ backgroundColor: '#ef4444', color: 'white' }}
              >
                Logout
              </button>
            </div>
          </div>
        </div>
      </nav>

      {/* Tabs */}
      <div className="bg-white border-b" style={{ backgroundColor: '#ffffff' }}>
        <div className="max-w-7xl mx-auto">
          <div className="flex gap-2">
            <button
              onClick={() => setActiveTab('overview')}
              className={`py-2 px-4 text-sm font-medium transition ${
                activeTab === 'overview'
                  ? 'border-b-2'
                  : 'text-gray-500 hover:text-gray-700'
              }`}
              style={activeTab === 'overview' ? { borderColor: '#2563eb', color: '#2563eb' } : {}}
            >
              Class Overview
            </button>
            <button
              onClick={() => setActiveTab('mastery')}
              className={`py-2 px-4 text-sm font-medium transition ${
                activeTab === 'mastery'
                  ? 'border-b-2'
                  : 'text-gray-500 hover:text-gray-700'
              }`}
              style={activeTab === 'mastery' ? { borderColor: '#2563eb', color: '#2563eb' } : {}}
            >
              Mastery Tracker
            </button>
            <button
              onClick={() => setActiveTab('curriculum')}
              className={`py-2 px-4 text-sm font-medium transition ${
                activeTab === 'curriculum'
                  ? 'border-b-2'
                  : 'text-gray-500 hover:text-gray-700'
              }`}
              style={activeTab === 'curriculum' ? { borderColor: '#2563eb', color: '#2563eb' } : {}}
            >
              Curriculum Search
            </button>
            <button
              onClick={() => setActiveTab('heatmap')}
              className={`py-2 px-4 text-sm font-medium transition ${
                activeTab === 'heatmap'
                  ? 'border-b-2'
                  : 'text-gray-500 hover:text-gray-700'
              }`}
              style={activeTab === 'heatmap' ? { borderColor: '#2563eb', color: '#2563eb' } : {}}
            >
              Gap Heatmap
            </button>
            <button
              onClick={() => setActiveTab('students')}
              className={`py-2 px-4 text-sm font-medium transition ${
                activeTab === 'students'
                  ? 'border-b-2'
                  : 'text-gray-500 hover:text-gray-700'
              }`}
              style={activeTab === 'students' ? { borderColor: '#2563eb', color: '#2563eb' } : {}}
            >
              Students
            </button>
            <button
              onClick={() => setActiveTab('quizzes')}
              className={`py-2 px-4 text-sm font-medium transition ${
                activeTab === 'quizzes'
                  ? 'border-b-2'
                  : 'text-gray-500 hover:text-gray-700'
              }`}
              style={activeTab === 'quizzes' ? { borderColor: '#2563eb', color: '#2563eb' } : {}}
            >
              Quizzes
            </button>
            <button
              onClick={() => setActiveTab('approvals')}
              className={`py-2 px-4 text-sm font-medium transition ${
                activeTab === 'approvals'
                  ? 'border-b-2'
                  : 'text-gray-500 hover:text-gray-700'
              }`}
              style={activeTab === 'approvals' ? { borderColor: '#2563eb', color: '#2563eb' } : {}}
            >
              Pending Approvals ({pendingMaterials.length})
            </button>
            <button
              onClick={() => { setActiveTab('analytics'); loadAnalytics(); }}
              className={`py-2 px-4 text-sm font-medium transition ${
                activeTab === 'analytics'
                  ? 'border-b-2'
                  : 'text-gray-500 hover:text-gray-700'
              }`}
              style={activeTab === 'analytics' ? { borderColor: '#2563eb', color: '#2563eb' } : {}}
            >
              Analytics
            </button>
          </div>
        </div>
      </div>

      {/* Content */}
      <div className="max-w-7xl mx-auto px-4 py-4">
        {error && (
          <div className="mb-4 px-4 py-3 rounded" style={{ backgroundColor: '#fef2f2', color: '#991b1b', border: '1px solid #fecaca' }}>
            {error}
          </div>
        )}

        {activeTab === 'overview' && (
          <OverviewTab
            totalStudents={totalStudents}
            quizzes={quizzes}
            pendingMaterials={pendingMaterials}
            masteryOverview={masteryOverview}
            getMasteryBarColor={getMasteryBarColor}
            onGenerateBatch={handleGenerateBatchForStruggling}
            batchProgress={batchGenProgress}
            batchSummary={batchGenSummary}
            setBatchSummary={setBatchGenSummary}
          />
        )}

        {activeTab === 'mastery' && (
          <MasteryTab
            masteryOverview={masteryOverview}
            expandedTopic={expandedTopic}
            setExpandedTopic={setExpandedTopic}
            getMasteryBarColor={getMasteryBarColor}
          />
        )}

        {activeTab === 'curriculum' && (
          <CurriculumTab
            curriculumQuery={curriculumQuery}
            setCurriculumQuery={setCurriculumQuery}
            curriculumLoading={curriculumLoading}
            curriculumSearched={curriculumSearched}
            handleCurriculumSearch={handleCurriculumSearch}
            curriculumResults={curriculumResults}
            onGenerateFromSearch={handleGenerateFromSearchResult}
            generatingIds={curriculumGeneratingIds}
          />
        )}

        {activeTab === 'heatmap' && (
          <HeatmapTab
            heatmapData={heatmapData}
            heatmapGradeFilter={heatmapGradeFilter}
            setHeatmapGradeFilter={setHeatmapGradeFilter}
            heatmapSort={heatmapSort}
            setHeatmapSort={setHeatmapSort}
            setSelectedHeatmapTopic={setSelectedHeatmapTopic}
          />
        )}

        {activeTab === 'students' && (
          <StudentsTab
            students={students}
            selectedStudent={selectedStudent}
            handleStudentSelect={handleStudentSelect}
            studentGaps={studentGaps}
            generateTopic={generateTopic}
            setGenerateTopic={setGenerateTopic}
            generateDifficulty={generateDifficulty}
            setGenerateDifficulty={setGenerateDifficulty}
            isGenerating={isGenerating}
            generateStatus={generateStatus}
            handleGenerateMaterial={handleGenerateMaterial}
            handleGenerateForWeakness={handleGenerateForWeakness}
            getWeaknessColor={getWeaknessColor}
          />
        )}

        {activeTab === 'quizzes' && (
          <QuizzesTab
            quizzes={quizzes}
            setShowCreateQuiz={setShowCreateQuiz}
            setShowAIQuizModal={setShowAIQuizModal}
            setAiQuizError={setAiQuizError}
            setAiQuizResult={setAiQuizResult}
            handleOpenTopicGenerator={handleOpenTopicGenerator}
            handleViewQuizResults={handleViewQuizResults}
            handleEditQuiz={handleEditQuiz}
            handleDeleteQuiz={handleDeleteQuiz}
          />
        )}

        {activeTab === 'approvals' && (
          <ApprovalsTab
            pendingMaterials={pendingMaterials}
            students={students}
            handleApproveMaterial={handleApproveMaterial}
            setShowRejectConfirm={setShowRejectConfirm}
          />
        )}

        {/* Analytics Tab */}
        {activeTab === 'analytics' && (
          <div>
            <div className="flex justify-between items-center mb-4">
              <h2 className="text-xl font-bold">Material & Platform Analytics</h2>
              <button
                onClick={loadAnalytics}
                disabled={analyticsLoading}
                className="px-3 py-1.5 text-sm rounded-md text-white hover:opacity-90"
                style={{ backgroundColor: '#2563eb' }}
              >
                {analyticsLoading ? 'Refreshing…' : 'Refresh'}
              </button>
            </div>

            <div className="bg-white rounded-lg shadow-sm p-4 mb-4" style={{ backgroundColor: '#ffffff' }}>
              <h3 className="text-sm font-semibold mb-3 text-gray-700">Material Quality & Approval Summary</h3>
              {analyticsData ? (
                <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                  {[
                    { label: 'Total Materials', val: analyticsData.approval_stats?.total_materials || 0, color: '#2563eb' },
                    { label: 'Approved', val: analyticsData.approval_stats?.approved || 0, color: '#10b981' },
                    { label: 'Pending', val: analyticsData.approval_stats?.pending || 0, color: '#f59e0b' },
                    { label: 'Rejected', val: analyticsData.approval_stats?.rejected || 0, color: '#ef4444' },
                  ].map(card => (
                    <div key={card.label} className="rounded-lg p-3 border" style={{ borderColor: '#e5e7eb' }}>
                      <div className="text-2xl font-bold" style={{ color: card.color }}>{card.val}</div>
                      <div className="text-xs text-gray-500">{card.label}</div>
                    </div>
                  ))}
                </div>
              ) : (
                <p className="text-sm text-gray-500">Click Refresh to load analytics data.</p>
              )}
            </div>

            <div className="bg-white rounded-lg shadow-sm p-4 mb-4" style={{ backgroundColor: '#ffffff' }}>
              <h3 className="text-sm font-semibold mb-3 text-gray-700">Most Generated Topics</h3>
              {analyticsData?.top_topics?.length > 0 ? (
                <div className="space-y-2">
                  {analyticsData.top_topics.map((t, i) => (
                    <div key={t.topic} className="flex items-center gap-3">
                      <span className="text-xs font-bold w-5" style={{ color: '#9ca3af' }}>{i + 1}.</span>
                      <span className="text-sm flex-1 text-gray-800">{t.topic}</span>
                      <div className="flex items-center gap-1">
                        <div className="w-28 bg-gray-200 rounded-full h-2">
                          <div
                            className="h-2 rounded-full"
                            style={{ width: `${Math.min(100, t.count * 20)}%`, backgroundColor: '#2563eb' }}
                          />
                        </div>
                        <span className="text-xs text-gray-500 w-12 text-right">{t.count}×</span>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <p className="text-sm text-gray-500">No generation history yet. Start generating material to see trends.</p>
              )}
            </div>

            <div className="bg-white rounded-lg shadow-sm p-4 mb-4" style={{ backgroundColor: '#ffffff' }}>
              <h3 className="text-sm font-semibold mb-3 text-gray-700">Topics Students Struggle With Most</h3>
              {analyticsData?.struggling_topics?.length > 0 ? (
                <div className="space-y-2">
                  {analyticsData.struggling_topics.map((t) => (
                    <div
                      key={t.topic_id}
                      className="flex items-center gap-3 p-2 rounded-lg border"
                      style={{ borderColor: '#e5e7eb' }}
                    >
                      <div
                        className="w-9 h-9 rounded-full flex items-center justify-center text-xs font-bold text-white flex-shrink-0"
                        style={{ backgroundColor: t.avg_score < 40 ? '#ef4444' : '#f59e0b' }}
                      >
                        {t.avg_score.toFixed(0)}%
                      </div>
                      <div className="flex-1">
                        <div className="text-sm font-medium text-gray-800">{t.topic_name}</div>
                        <div className="text-xs text-gray-500">Grade {t.grade_level} · {t.num_students} students affected</div>
                      </div>
                      <button
                        onClick={() => { setShowTopicGeneratorModal(true); setTopicInput(t.topic_name); }}
                        className="px-3 py-1 text-xs rounded-md text-white hover:opacity-90"
                        style={{ backgroundColor: '#2563eb' }}
                      >
                        Generate Material
                      </button>
                    </div>
                  ))}
                </div>
              ) : (
                <p className="text-sm text-gray-500">All topics are performing well! Great job, class.</p>
              )}
            </div>

            <div className="bg-white rounded-lg shadow-sm p-4 mb-4" style={{ backgroundColor: '#ffffff' }}>
              <h3 className="text-sm font-semibold mb-2 text-gray-700">Platform Summary</h3>
              <div className="grid grid-cols-3 gap-3">
                <div className="text-center p-3 bg-blue-50 rounded-lg">
                  <div className="text-lg font-bold" style={{ color: '#2563eb' }}>
                    {analyticsData?.ai_quizzes_generated || 0}
                  </div>
                  <div className="text-xs text-gray-500">AI Quizzes Generated</div>
                </div>
                <div className="text-center p-3 bg-green-50 rounded-lg">
                  <div className="text-lg font-bold" style={{ color: '#10b981' }}>
                    {analyticsData?.approval_stats?.total_helpful || 0}
                  </div>
                  <div className="text-xs text-gray-500">Helpful Ratings</div>
                </div>
                <div className="text-center p-3 bg-red-50 rounded-lg">
                  <div className="text-lg font-bold" style={{ color: '#ef4444' }}>
                    {analyticsData?.approval_stats?.total_not_helpful || 0}
                  </div>
                  <div className="text-xs text-gray-500">Not Helpful Ratings</div>
                </div>
              </div>
            </div>

            <div className="bg-white rounded-lg shadow-sm p-4" style={{ backgroundColor: '#ffffff' }}>
              <h3 className="text-sm font-semibold mb-2 text-gray-700">Batch Material Generation</h3>
              <p className="text-xs text-gray-500 mb-3">
                Generate practice material for one topic for every student in your assigned grade.
                Each student gets their own copy (pending your approval).
              </p>
              <div className="flex gap-3 items-end mb-3 flex-wrap">
                <div>
                  <label className="block text-xs text-gray-500 mb-1">Grade Level</label>
                  <select
                    value={String(assignedGradeNum || batchGrade)}
                    disabled={!!assignedGradeNum}
                    onChange={(e) => setBatchGrade(e.target.value)}
                    className="border rounded px-3 py-1.5 text-sm focus:outline-none focus:ring-2 disabled:bg-gray-100"
                    style={{ borderColor: '#d1d5db' }}
                  >
                    <option value="9">Grade 9</option>
                    <option value="10">Grade 10</option>
                    <option value="11">Grade 11</option>
                    <option value="12">Grade 12</option>
                  </select>
                </div>
                <div className="flex-1 min-w-[200px]">
                  <label className="block text-xs text-gray-500 mb-1">Topic</label>
                  <input
                    type="text"
                    value={batchTopic}
                    onChange={(e) => setBatchTopic(e.target.value)}
                    placeholder="e.g. Linear equations"
                    className="w-full border rounded px-3 py-1.5 text-sm focus:outline-none focus:ring-2"
                    style={{ borderColor: '#d1d5db' }}
                  />
                </div>
                <div>
                  <label className="block text-xs text-gray-500 mb-1">Difficulty</label>
                  <select
                    value={batchDiff}
                    onChange={(e) => setBatchDiff(e.target.value)}
                    className="border rounded px-3 py-1.5 text-sm focus:outline-none focus:ring-2"
                    style={{ borderColor: '#d1d5db' }}
                  >
                    <option value="easy">Easy</option>
                    <option value="medium">Medium</option>
                    <option value="hard">Hard</option>
                  </select>
                </div>
                <button
                  onClick={handleBatchGenerate}
                  disabled={batchLoading}
                  className="px-4 py-1.5 text-sm rounded-md text-white disabled:opacity-50"
                  style={{ backgroundColor: '#7c3aed' }}
                >
                  {batchLoading ? 'Generating…' : 'Generate for All Students'}
                </button>
              </div>
              {batchResult && (
                <div
                  className="rounded p-3 text-sm"
                  style={{ backgroundColor: '#ecfdf5', border: '1px solid #a7f3d0', color: '#065f46' }}
                >
                  {batchResult.message}: {batchResult.generated} material(s) for{' '}
                  {batchResult.total_students || 0} student{batchResult.total_students !== 1 ? 's' : ''}
                  {batchResult.topic_name ? ` on "${batchResult.topic_name}"` : ''}.
                  {batchResult.failed > 0 && <span> ({batchResult.failed} failed)</span>}
                  <span className="block mt-1 text-xs">Approve in Pending Approvals so students can access them.</span>
                </div>
              )}
            </div>
          </div>
        )}
      </div>

      {/* Create Quiz Modal */}
      {showCreateQuiz && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-lg shadow-xl w-full max-w-2xl max-h-[85vh] overflow-y-auto p-4" style={{ backgroundColor: '#ffffff' }}>
            <h2 className="text-lg font-bold mb-3">Create New Quiz</h2>
            <form onSubmit={handleCreateQuiz}>
              <div className="grid grid-cols-2 gap-3 mb-3">
                <div>
                  <label className="block text-gray-700 text-sm font-medium mb-1">Quiz Title</label>
                  <input
                    type="text"
                    value={quizForm.title}
                    onChange={(e) => setQuizForm({ ...quizForm, title: e.target.value })}
                    className="w-full px-2 py-1.5 text-sm border rounded focus:outline-none focus:ring-2"
                    style={{ borderColor: '#d1d5db' }}
                    required
                  />
                </div>
                <div>
                  <label className="block text-gray-700 text-sm font-medium mb-1">Topic</label>
                  <select
                    value={quizForm.topic_id}
                    onChange={(e) => setQuizForm({ ...quizForm, topic_id: e.target.value })}
                    className="w-full px-2 py-1.5 text-sm border rounded focus:outline-none focus:ring-2"
                    style={{ borderColor: '#d1d5db' }}
                    required
                  >
                    <option value="">Select Topic</option>
                    <option value="1">Algebra</option>
                    <option value="2">Limits</option>
                    <option value="3">Integration</option>
                  </select>
                </div>
              </div>
              
              <div className="grid grid-cols-2 gap-3 mb-4">
                <div>
                  <label className="block text-gray-700 text-sm font-medium mb-1">Time Limit (minutes)</label>
                  <input
                    type="number"
                    value={quizForm.time_limit}
                    onChange={(e) => setQuizForm({ ...quizForm, time_limit: e.target.value })}
                    className="w-full px-2 py-1.5 text-sm border rounded focus:outline-none focus:ring-2"
                    style={{ borderColor: '#d1d5db' }}
                  />
                </div>
                <div className="flex items-center">
                  <span className="text-sm text-gray-600">{quizForm.questions.length} questions added</span>
                </div>
              </div>

              <div className="border rounded-lg p-3 mb-4" style={{ borderColor: '#e5e7eb' }}>
                <h3 className="text-sm font-semibold mb-2">Add Question</h3>
                <div className="mb-2">
                  <input
                    type="text"
                    placeholder="Enter question text..."
                    value={newQuestion.question_text}
                    onChange={(e) => setNewQuestion({ ...newQuestion, question_text: e.target.value })}
                    className="w-full px-2 py-1.5 text-sm border rounded"
                    style={{ borderColor: '#d1d5db' }}
                  />
                </div>
                <FilePicker
                  context="quiz"
                  imagesOnly
                  files={newQuestionImageFile}
                  onChange={(files) => setNewQuestionImageFile(files.slice(0, 1))}
                  label="Question image (optional — shown clearly to students in the quiz)"
                />
                <div className="grid grid-cols-2 gap-2 mb-2">
                  <div className="flex items-center gap-1">
                    <span className="text-xs text-gray-500 w-4">A:</span>
                    <input
                      type="text"
                      placeholder="Option A"
                      value={newQuestion.option_a}
                      onChange={(e) => setNewQuestion({ ...newQuestion, option_a: e.target.value })}
                      className="flex-1 px-2 py-1 text-xs border rounded"
                    />
                  </div>
                  <div className="flex items-center gap-1">
                    <span className="text-xs text-gray-500 w-4">B:</span>
                    <input
                      type="text"
                      placeholder="Option B"
                      value={newQuestion.option_b}
                      onChange={(e) => setNewQuestion({ ...newQuestion, option_b: e.target.value })}
                      className="flex-1 px-2 py-1 text-xs border rounded"
                    />
                  </div>
                  <div className="flex items-center gap-1">
                    <span className="text-xs text-gray-500 w-4">C:</span>
                    <input
                      type="text"
                      placeholder="Option C"
                      value={newQuestion.option_c}
                      onChange={(e) => setNewQuestion({ ...newQuestion, option_c: e.target.value })}
                      className="flex-1 px-2 py-1 text-xs border rounded"
                    />
                  </div>
                  <div className="flex items-center gap-1">
                    <span className="text-xs text-gray-500 w-4">D:</span>
                    <input
                      type="text"
                      placeholder="Option D"
                      value={newQuestion.option_d}
                      onChange={(e) => setNewQuestion({ ...newQuestion, option_d: e.target.value })}
                      className="flex-1 px-2 py-1 text-xs border rounded"
                    />
                  </div>
                </div>
                <div className="flex items-center gap-2 mb-2">
                  <span className="text-xs text-gray-600">Correct Answer:</span>
                  <select
                    value={newQuestion.correct_answer}
                    onChange={(e) => setNewQuestion({ ...newQuestion, correct_answer: e.target.value })}
                    className="px-2 py-1 text-xs border rounded"
                  >
                    <option value="A">A</option>
                    <option value="B">B</option>
                    <option value="C">C</option>
                    <option value="D">D</option>
                  </select>
                </div>
                <button
                  type="button"
                  onClick={handleAddQuestion}
                  className="px-3 py-1.5 text-xs rounded text-white"
                  style={{ backgroundColor: '#10b981' }}
                >
                  + Add Question
                </button>
              </div>

              {quizForm.questions.length > 0 && (
                <div className="mb-4">
                  <h3 className="text-sm font-semibold mb-2">Questions ({quizForm.questions.length})</h3>
                  <div className="space-y-2 max-h-40 overflow-y-auto">
                    {quizForm.questions.map((q, idx) => (
                      <div key={idx} className="flex items-start justify-between p-2 rounded" style={{ backgroundColor: '#f9fafb' }}>
                        <div className="flex-1">
                          <p className="text-xs font-medium">{idx + 1}. {q.question_text.substring(0, 60)}...</p>
                          <p className="text-xs text-gray-500">Answer: {q.correct_answer}{q.question_image ? ' · 📷 has image' : ''}</p>
                          {q.question_image && (
                            <img src={resolveUploadUrl(q.question_image)} alt="" className="mt-1 h-12 rounded border object-cover" />
                          )}
                        </div>
                        <button
                          type="button"
                          onClick={() => handleRemoveQuestion(idx)}
                          className="text-red-500 text-xs hover:text-red-700 ml-2"
                        >
                          ✕
                        </button>
                      </div>
                    ))}
                  </div>
                </div>
              )}
              
              <div className="flex justify-end gap-2">
                <button
                  type="button"
                  onClick={() => { setShowCreateQuiz(false); setQuizForm({ title: '', topic_id: '', total_marks: '', time_limit: '30', questions: [] }); }}
                  className="px-3 py-1.5 text-sm rounded-md hover:bg-gray-200"
                  style={{ backgroundColor: '#e5e7eb' }}
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-3 py-1.5 text-sm rounded-md text-white"
                  style={{ backgroundColor: '#2563eb' }}
                >
                  Create Quiz ({quizForm.questions.length} questions)
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Edit Quiz Modal */}
      {showEditQuiz && editingQuiz && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-lg shadow-xl w-full max-w-2xl max-h-[85vh] overflow-y-auto p-4">
            <h2 className="text-lg font-bold mb-3">Edit Quiz</h2>
            <form onSubmit={(e) => { e.preventDefault(); handleUpdateQuiz(); }}>
              <div className="grid grid-cols-2 gap-3 mb-3">
                <div>
                  <label className="block text-gray-700 text-sm font-medium mb-1">Quiz Title</label>
                  <input
                    type="text"
                    value={quizForm.title}
                    onChange={(e) => setQuizForm({ ...quizForm, title: e.target.value })}
                    className="w-full px-2 py-1.5 text-sm border rounded"
                    required
                  />
                </div>
                <div>
                  <label className="block text-gray-700 text-sm font-medium mb-1">Topic</label>
                  <select
                    value={quizForm.topic_id}
                    onChange={(e) => setQuizForm({ ...quizForm, topic_id: e.target.value })}
                    className="w-full px-2 py-1.5 text-sm border rounded"
                    required
                  >
                    <option value="">Select Topic</option>
                    <option value="1">Algebra</option>
                    <option value="2">Limits</option>
                    <option value="3">Integration</option>
                  </select>
                </div>
              </div>
              
              <div className="grid grid-cols-2 gap-3 mb-4">
                <div>
                  <label className="block text-gray-700 text-sm font-medium mb-1">Time Limit (minutes)</label>
                  <input
                    type="number"
                    value={quizForm.time_limit}
                    onChange={(e) => setQuizForm({ ...quizForm, time_limit: e.target.value })}
                    className="w-full px-2 py-1.5 text-sm border rounded"
                  />
                </div>
                <div className="flex items-center">
                  <span className="text-sm text-gray-600">{quizForm.questions.length} questions</span>
                </div>
              </div>

              <div className="border rounded-lg p-3 mb-4">
                <h3 className="text-sm font-semibold mb-2">Add Question</h3>
                <div className="mb-2">
                  <input
                    type="text"
                    placeholder="Enter question text..."
                    value={newQuestion.question_text}
                    onChange={(e) => setNewQuestion({ ...newQuestion, question_text: e.target.value })}
                    className="w-full px-2 py-1.5 text-sm border rounded"
                  />
                </div>
                <FilePicker
                  context="quiz"
                  imagesOnly
                  files={newQuestionImageFile}
                  onChange={(files) => setNewQuestionImageFile(files.slice(0, 1))}
                  label="Question image (optional)"
                />
                <div className="grid grid-cols-2 gap-2 mb-2">
                  <div className="flex items-center gap-1">
                    <span className="text-xs text-gray-500 w-4">A:</span>
                    <input type="text" placeholder="Option A" value={newQuestion.option_a} onChange={(e) => setNewQuestion({ ...newQuestion, option_a: e.target.value })} className="flex-1 px-2 py-1 text-xs border rounded" />
                  </div>
                  <div className="flex items-center gap-1">
                    <span className="text-xs text-gray-500 w-4">B:</span>
                    <input type="text" placeholder="Option B" value={newQuestion.option_b} onChange={(e) => setNewQuestion({ ...newQuestion, option_b: e.target.value })} className="flex-1 px-2 py-1 text-xs border rounded" />
                  </div>
                  <div className="flex items-center gap-1">
                    <span className="text-xs text-gray-500 w-4">C:</span>
                    <input type="text" placeholder="Option C" value={newQuestion.option_c} onChange={(e) => setNewQuestion({ ...newQuestion, option_c: e.target.value })} className="flex-1 px-2 py-1 text-xs border rounded" />
                  </div>
                  <div className="flex items-center gap-1">
                    <span className="text-xs text-gray-500 w-4">D:</span>
                    <input type="text" placeholder="Option D" value={newQuestion.option_d} onChange={(e) => setNewQuestion({ ...newQuestion, option_d: e.target.value })} className="flex-1 px-2 py-1 text-xs border rounded" />
                  </div>
                </div>
                <div className="flex items-center gap-2 mb-2">
                  <span className="text-xs text-gray-600">Correct:</span>
                  <select value={newQuestion.correct_answer} onChange={(e) => setNewQuestion({ ...newQuestion, correct_answer: e.target.value })} className="px-2 py-1 text-xs border rounded">
                    <option value="A">A</option>
                    <option value="B">B</option>
                    <option value="C">C</option>
                    <option value="D">D</option>
                  </select>
                </div>
                <button type="button" onClick={handleAddQuestion} className="px-3 py-1.5 text-xs rounded text-white" style={{ backgroundColor: '#10b981' }}>+ Add Question</button>
              </div>

              {quizForm.questions.length > 0 && (
                <div className="mb-4">
                  <h3 className="text-sm font-semibold mb-2">Questions ({quizForm.questions.length})</h3>
                  <div className="space-y-2 max-h-40 overflow-y-auto">
                    {quizForm.questions.map((q, idx) => (
                      <div key={idx} className="flex items-start justify-between p-2 rounded" style={{ backgroundColor: '#f9fafb' }}>
                        <div className="flex-1">
                          <p className="text-xs font-medium">{idx + 1}. {q.question_text.substring(0, 60)}...</p>
                          <p className="text-xs text-gray-500">Answer: {q.correct_answer}{q.question_image ? ' · 📷' : ''}</p>
                          {q.question_image && (
                            <img src={resolveUploadUrl(q.question_image)} alt="" className="mt-1 h-12 rounded border object-cover" />
                          )}
                        </div>
                        <button type="button" onClick={() => handleRemoveQuestion(idx)} className="text-red-500 text-xs hover:text-red-700 ml-2">✕</button>
                      </div>
                    ))}
                  </div>
                </div>
              )}
              
              <div className="flex justify-between">
                <button type="button" onClick={() => { setShowEditQuiz(false); setEditingQuiz(null); setQuizForm({ title: '', topic_id: '', total_marks: '', time_limit: '30', questions: [] }); setNewQuestionImageFile([]); }} className="px-3 py-1.5 text-sm rounded-md hover:bg-gray-200" style={{ backgroundColor: '#e5e7eb' }}>Cancel</button>
                <button type="submit" className="px-3 py-1.5 text-sm rounded-md text-white" style={{ backgroundColor: '#2563eb' }}>Save Changes</button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* View Results Modal */}
      {showResultsModal && selectedQuizResults && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg shadow-xl w-full max-w-2xl max-h-[80vh] overflow-y-auto p-4" style={{ backgroundColor: '#ffffff' }}>
            <div className="flex justify-between items-center mb-3">
              <h2 className="text-xl font-bold">Quizzes</h2>
              <div className="flex gap-2">
                <button
                  onClick={() => setShowCreateQuiz(true)}
                  className="px-3 py-1.5 text-sm rounded-md transition text-white"
                  style={{ backgroundColor: '#2563eb' }}
                >
                  + Create New Quiz
                </button>
                <button
                  onClick={() => { setShowAIQuizModal(true); setAiQuizError(''); setAiQuizResult(null); }}
                  className="px-3 py-1.5 text-sm rounded-md transition text-white"
                  style={{ backgroundColor: '#7c3aed' }}
                >
                  ✦ Generate AI Quiz
                </button>
                <button
                  onClick={handleOpenTopicGenerator}
                  className="px-3 py-1.5 text-sm rounded-md transition text-white"
                  style={{ backgroundColor: '#059669' }}
                >
                  Generate Material by Topic
                </button>
              </div>
            </div>
            
            {selectedQuizResults.results.length > 0 ? (
              <table className="w-full text-sm">
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
                    <tr key={idx} className="border-b even:bg-gray-50">
                      <td className="p-2">{result.student_name}</td>
                      <td className="p-2">{result.score} / {result.total_marks}</td>
                      <td className="p-2">
                        <span className={`px-2 py-0.5 rounded text-xs ${
                          (result.score / result.total_marks) * 100 >= 70 
                            ? 'bg-green-100 text-green-800' 
                            : 'bg-red-100 text-red-800'
                        }`}>
                          {Math.min(100, Math.round((result.score / result.total_marks) * 100))}%
                        </span>
                      </td>
                      <td className="p-2 text-xs text-gray-500">
                        {new Date(result.completed_at).toLocaleDateString()}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            ) : (
              <div className="text-center text-gray-500 py-6">
                No submissions yet for this quiz
              </div>
            )}
          </div>
        </div>
      )}

      {/* Reject Confirmation Modal */}
      {showRejectConfirm && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg shadow-xl w-full max-w-md p-4" style={{ backgroundColor: '#ffffff' }}>
            <h2 className="text-lg font-bold mb-3">Confirm Rejection</h2>
            <p className="text-gray-600 mb-4 text-sm">
              Are you sure you want to reject this material? This action cannot be undone.
            </p>
            <div className="flex justify-end gap-2">
              <button
                onClick={() => setShowRejectConfirm(null)}
                className="px-3 py-1.5 text-sm rounded-md hover:bg-gray-200"
                style={{ backgroundColor: '#e5e7eb' }}
              >
                Cancel
              </button>
              <button
                onClick={() => handleRejectMaterial(showRejectConfirm)}
                className="px-3 py-1.5 text-sm rounded-md text-white"
                style={{ backgroundColor: '#ef4444' }}
              >
                Reject
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Generate Material by Topic Modal */}
      {showTopicGeneratorModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-lg shadow-xl w-full max-w-2xl max-h-[85vh] overflow-y-auto p-4" style={{ backgroundColor: '#ffffff' }}>
            <div className="flex justify-between items-center mb-4">
              <h2 className="text-lg font-bold">Generate Material by Topic</h2>
              <button onClick={handleCloseTopicGenerator} className="text-gray-500 hover:text-gray-700 text-lg leading-none">&times;</button>
            </div>

            {topicGenStep === 1 && (
              <div>
                <p className="text-xs text-gray-500 mb-3">Type any math topic to search the curriculum and generate practice material.</p>

                <div className="space-y-3">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Topic</label>
                    <div className="relative">
                    <input
                      type="text"
                      value={topicInput}
                      onChange={(e) => handleTopicInputChange(e.target.value, true)}
                      onFocus={() => topicInput.length >= 2 && setTopicSuggestionVisible(true)}
                      placeholder="e.g., Solving linear equations"
                      className="w-full px-3 py-2 text-sm border rounded focus:outline-none focus:ring-2"
                      style={{ borderColor: '#d1d5db' }}
                    />
                    {topicSuggestionVisible && aiQuizSuggestions.length > 0 && (
                      <ul className="absolute z-10 w-full mt-1 bg-white border rounded shadow-lg max-h-40 overflow-y-auto">
                        {aiQuizSuggestions.map((s, i) => (
                          <li key={i}>
                            <button
                              type="button"
                              className="w-full text-left px-3 py-2 text-sm hover:bg-blue-50"
                              onClick={() => {
                                setTopicInput(s.topic);
                                setTopicSuggestionVisible(false);
                                setAiQuizSuggestions([]);
                                if (s.grade_level) setTopicGradeLevel(String(s.grade_level));
                              }}
                            >
                              {s.topic}
                              {s.grade_level && <span className="text-xs text-gray-500 ml-2">Grade {s.grade_level}</span>}
                            </button>
                          </li>
                        ))}
                      </ul>
                    )}
                    </div>
                  </div>
                  <div className="grid grid-cols-2 gap-3">
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">Grade Level</label>
                      <select
                        value={String(assignedGradeNum || topicGradeLevel)}
                        disabled={!!assignedGradeNum}
                        onChange={(e) => setTopicGradeLevel(e.target.value)}
                        className="w-full px-3 py-2 text-sm border rounded focus:outline-none focus:ring-2 disabled:bg-gray-100"
                        style={{ borderColor: '#d1d5db' }}
                      >
                        <option value="9">Grade 9</option>
                        <option value="10">Grade 10</option>
                        <option value="11">Grade 11</option>
                        <option value="12">Grade 12</option>
                      </select>
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">Difficulty</label>
                      <select
                        value={topicDifficulty}
                        onChange={(e) => setTopicDifficulty(e.target.value)}
                        className="w-full px-3 py-2 text-sm border rounded focus:outline-none focus:ring-2"
                        style={{ borderColor: '#d1d5db' }}
                      >
                        <option value="easy">Easy</option>
                        <option value="medium">Medium</option>
                        <option value="hard">Hard</option>
                      </select>
                    </div>
                  </div>
                  <label className="flex items-center gap-2 text-sm text-gray-700 cursor-pointer">
                    <input
                      type="checkbox"
                      checked={topicGenForAll}
                      onChange={(e) => {
                        setTopicGenForAll(e.target.checked);
                        if (e.target.checked) setTopicGenStudentId('');
                      }}
                    />
                    Generate for all students in my grade ({assignedGradeNum || topicGradeLevel})
                  </label>
                  {!topicGenForAll && (
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">Assign to one student</label>
                      <select
                        value={topicGenStudentId}
                        onChange={(e) => setTopicGenStudentId(e.target.value)}
                        className="w-full px-3 py-2 text-sm border rounded focus:outline-none focus:ring-2"
                        style={{ borderColor: '#d1d5db' }}
                      >
                        <option value="">Select a student…</option>
                        {students.map((s) => (
                          <option key={s.user_id} value={String(s.user_id)}>
                            {s.full_name}
                          </option>
                        ))}
                      </select>
                    </div>
                  )}
                </div>

                <div className="flex justify-end gap-2 mt-4">
                  <button onClick={handleCloseTopicGenerator} className="px-3 py-1.5 text-sm rounded-md hover:bg-gray-200" style={{ backgroundColor: '#e5e7eb' }}>Cancel</button>
                  <button
                    onClick={handleSearchCurriculumPreview}
                    disabled={!topicInput.trim() || topicGenLoading}
                    className="px-4 py-1.5 text-sm rounded-md transition text-white disabled:opacity-50 disabled:cursor-not-allowed"
                    style={{ backgroundColor: '#2563eb' }}
                  >
                    {topicGenLoading ? 'Searching...' : 'Search Curriculum'}
                  </button>
                </div>
              </div>
            )}

            {topicGenStep === 2 && topicGenStatus !== 'generated' && (
              <div>
                <p className="text-sm text-gray-600 mb-2">
                  Curriculum search results for <strong>{topicInput}</strong> (Grade {topicGradeLevel}):
                </p>

                {topicGenStatus === 'no_results' && (
                  <div className="bg-yellow-50 border border-yellow-200 rounded p-3 mb-3">
                    <p className="text-sm text-yellow-800">{topicGenPreview}</p>
                  </div>
                )}

                {topicGenStatus === 'error' && (
                  <div className="bg-red-50 border border-red-200 rounded p-3 mb-3">
                    <p className="text-sm text-red-700">{topicGenPreview}</p>
                  </div>
                )}

                {topicGenStatus === 'found' && (
                  <div className="bg-gray-50 rounded-lg p-3 mb-3 max-h-60 overflow-y-auto" style={{ backgroundColor: '#f9fafb' }}>
                    <div className="text-xs text-gray-600 mb-2 font-medium">Curriculum Content Preview:</div>
                    <MathContent html={topicGenPreview} />
                  </div>
                )}

                <div className="flex justify-between mt-4">
                  <button onClick={() => { setTopicGenStep(1); setTopicGenPreview(''); setTopicGenStatus(''); }} className="px-3 py-1.5 text-sm rounded-md hover:bg-gray-200" style={{ backgroundColor: '#e5e7eb' }}>Back</button>
                  <div className="flex gap-2">
                    <button onClick={handleCloseTopicGenerator} className="px-3 py-1.5 text-sm rounded-md hover:bg-gray-200" style={{ backgroundColor: '#e5e7eb' }}>Cancel</button>
                    <button
                      onClick={handleGenerateMaterialByTopic}
                      disabled={topicGenLoading || (!topicGenForAll && !topicGenStudentId)}
                      className="px-4 py-1.5 text-sm rounded-md transition text-white disabled:opacity-50"
                      style={{ backgroundColor: '#7c3aed' }}
                    >
                      {topicGenLoading ? 'Generating...' : 'Generate Material'}
                    </button>
                  </div>
                </div>
              </div>
            )}

            {topicGenStep === 3 && topicGenStatus === 'generated' && (
              <div>
                <MathContent html={topicGenPreview} className="mb-4" />
                <div className="flex justify-end gap-2">
                  <button onClick={handleCloseTopicGenerator} className="px-3 py-1.5 text-sm rounded-md hover:bg-gray-200" style={{ backgroundColor: '#e5e7eb' }}>Close</button>
                  <button onClick={() => { setShowRejectConfirm(null); setActiveTab('approvals'); }} className="px-4 py-1.5 text-sm rounded-md text-white" style={{ backgroundColor: '#2563eb' }}>Go to Pending Approvals</button>
                </div>
              </div>
            )}
          </div>
        </div>
      )}

      {/* AI Quiz Generation Modal */}
      {showAIQuizModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-lg shadow-xl w-full max-w-lg" style={{ backgroundColor: '#ffffff' }}>
            <div className="p-4 border-b flex justify-between items-center">
              <h2 className="text-lg font-bold">Generate AI Quiz</h2>
              <button
                onClick={() => { setShowAIQuizModal(false); setAiQuizError(''); setAiQuizResult(null); }}
                className="text-gray-500 hover:text-gray-700 text-lg leading-none"
              >
                &times;
              </button>
            </div>

            <div className="p-4 space-y-3">
              <p className="text-xs text-gray-500">
                AI generates a quiz from the curriculum via RAG search. All 6 textbooks are searched.
              </p>

              <div className="relative">
                <label className="block text-sm font-medium text-gray-700 mb-1">Topic</label>
                <input
                  type="text"
                  value={aiQuizTopic}
                  onChange={(e) => handleTopicInputChange(e.target.value)}
                  onFocus={() => aiQuizSuggestions.length > 0 && setTopicSuggestionVisible(true)}
                  onBlur={() => setTimeout(() => setTopicSuggestionVisible(false), 200)}
                  placeholder="e.g., Probability, Quadratic Equations, Derivatives"
                  className="w-full px-3 py-2 text-sm border rounded focus:outline-none focus:ring-2"
                  style={{ borderColor: '#d1d5db' }}
                />
                {topicSuggestionVisible && aiQuizSuggestions.length > 0 && (
                  <div className="absolute z-10 left-0 right-0 bg-white border rounded-b shadow-lg max-h-48 overflow-y-auto"
                       style={{ borderColor: '#d1d5db', top: '100%' }}>
                    {aiQuizSuggestions.map((s, i) => (
                      <button
                        key={i}
                        onMouseDown={() => selectSuggestion(s)}
                        className="w-full text-left px-3 py-2 text-sm hover:bg-blue-50 border-b"
                        style={{ borderColor: '#e5e7eb' }}
                      >
                        <span className="font-medium">{s.topic}</span>
                        {s.grade_level && (
                          <span className="ml-2 text-xs text-gray-500">Grade {s.grade_level}</span>
                        )}
                      </button>
                    ))}
                  </div>
                )}
              </div>

              <div className="grid grid-cols-3 gap-3">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Grade</label>
                  <select
                    value={aiQuizGrade}
                    onChange={(e) => setAiQuizGrade(e.target.value)}
                    className="w-full px-3 py-2 text-sm border rounded focus:outline-none focus:ring-2"
                    style={{ borderColor: '#d1d5db' }}
                  >
                    <option value="9">Grade 9</option>
                    <option value="10">Grade 10</option>
                    <option value="11">Grade 11</option>
                    <option value="12">Grade 12</option>
                  </select>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Questions</label>
                  <input
                    type="number"
                    min={3}
                    max={15}
                    value={aiQuizNumQ}
                    onChange={(e) => setAiQuizNumQ(Math.min(15, Math.max(3, parseInt(e.target.value) || 5)))}
                    className="w-full px-3 py-2 text-sm border rounded focus:outline-none focus:ring-2"
                    style={{ borderColor: '#d1d5db' }}
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Difficulty</label>
                  <select
                    value={aiQuizDiff}
                    onChange={(e) => setAiQuizDiff(e.target.value)}
                    className="w-full px-3 py-2 text-sm border rounded focus:outline-none focus:ring-2"
                    style={{ borderColor: '#d1d5db' }}
                  >
                    <option value="easy">Easy</option>
                    <option value="medium">Medium</option>
                    <option value="hard">Hard</option>
                  </select>
                </div>
              </div>

              {aiQuizError && (
                <div className="bg-red-50 border border-red-200 text-red-700 px-3 py-2 rounded text-sm">
                  {aiQuizError}
                </div>
              )}

              {aiQuizResult && (
                <div className="bg-green-50 border border-green-200 rounded p-3 text-sm">
                  <div className="font-semibold text-green-800 whitespace-pre-wrap">{aiQuizResult.title}</div>
                  <div className="text-xs text-green-700 mt-1">
                    Topic: {aiQuizResult.topic} · Grade {aiQuizResult.grade_level} · {aiQuizResult.num_questions} questions · {aiQuizResult.difficulty}
                  </div>
                  <div className="text-xs text-green-600 mt-1">{aiQuizResult.message}</div>
                  <div className="mt-2">
                    <div className="text-xs font-semibold text-gray-700 mb-1">Preview Questions:</div>
                    {aiQuizResult.questions?.map((q, i) => (
                      <div key={i} className="text-xs text-gray-700 mb-1">
                        Q{i + 1}. {q.question_text}
                      </div>
                    ))}
                  </div>
                </div>
              )}

              <div className="flex justify-end gap-2 pt-2">
                <button
                  onClick={() => { setShowAIQuizModal(false); setAiQuizError(''); setAiQuizResult(null); }}
                  className="px-3 py-1.5 text-sm rounded-md hover:bg-gray-200"
                  style={{ backgroundColor: '#e5e7eb' }}
                >
                  Cancel
                </button>
                <button
                  onClick={handleGenerateAIQuiz}
                  disabled={aiQuizLoading || !aiQuizTopic.trim()}
                  className="px-4 py-1.5 text-sm rounded-md text-white disabled:opacity-50"
                  style={{ backgroundColor: '#7c3aed' }}
                >
                  {aiQuizLoading ? 'Generating…' : 'Generate AI Quiz'}
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Struggling Students Modal */}
      {selectedHeatmapTopic && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg shadow-xl w-full max-w-lg max-h-[80vh] overflow-hidden flex flex-col" style={{ backgroundColor: '#ffffff' }}>
            <div
              className="p-4"
              style={{
                borderTopWidth: '4px',
                borderTopColor: selectedHeatmapTopic.status === 'good' ? '#10b981' : selectedHeatmapTopic.status === 'needs_attention' ? '#f59e0b' : '#ef4444'
              }}
            >
              <div className="flex justify-between items-start">
                <div>
                  <h2 className="text-lg font-bold">{selectedHeatmapTopic.topic_name}</h2>
                  <p className="text-xs text-gray-500">Grade {selectedHeatmapTopic.grade_level}</p>
                </div>
                <button
                  onClick={() => setSelectedHeatmapTopic(null)}
                  className="text-gray-400 hover:text-gray-600 text-2xl leading-none"
                >
                  &times;
                </button>
              </div>
              <div className="grid grid-cols-3 gap-3 mt-3">
                <div className="text-center">
                  <div className="text-xl font-bold text-green-600">{selectedHeatmapTopic.mastered_count}</div>
                  <div className="text-xs text-gray-500">Mastered</div>
                </div>
                <div className="text-center">
                  <div className="text-xl font-bold text-yellow-600">{selectedHeatmapTopic.struggling_count}</div>
                  <div className="text-xs text-gray-500">Struggling</div>
                </div>
                <div className="text-center">
                  <div className="text-xl font-bold text-gray-400">{selectedHeatmapTopic.untouched_count}</div>
                  <div className="text-xs text-gray-500">Not Started</div>
                </div>
              </div>
            </div>
            <div className="p-4 overflow-y-auto flex-1">
              <h3 className="font-medium mb-2 text-red-700 text-sm">Struggling Students</h3>
              {selectedHeatmapTopic.struggling_students && selectedHeatmapTopic.struggling_students.length > 0 ? (
                <div className="space-y-2">
                  {selectedHeatmapTopic.struggling_students.map((student) => (
                    <div key={student.student_id} className="flex justify-between items-center border rounded-lg p-2">
                      <div>
                        <div className="font-medium text-sm">{student.full_name}</div>
                        <div className="text-xs text-gray-500">Average: {student.avg_score}%</div>
                      </div>
                      <div className="flex items-center gap-2">
                        <span className={`px-1.5 py-0.5 rounded text-xs font-medium ${
                          student.avg_score < 40 ? 'bg-red-100 text-red-800' : 'bg-yellow-100 text-yellow-800'
                        }`}>
                          {student.avg_score < 40 ? 'Critical' : 'Needs Work'}
                        </span>
                        <button
                          onClick={() => {
                            setSelectedHeatmapTopic(null);
                            setActiveTab('students');
                            const found = students.find(s => s.user_id === student.student_id);
                            if (found) handleStudentSelect(found);
                          }}
                          className="text-blue-600 hover:text-blue-800 text-xs font-medium"
                        >
                          View
                        </button>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="text-center py-6 text-gray-500 text-sm">
                  No struggling students for this topic
                </div>
              )}
            </div>
            <div className="p-3 border-t bg-gray-50 flex justify-end">
              <button
                onClick={() => setSelectedHeatmapTopic(null)}
                className="px-3 py-1.5 text-sm rounded-md hover:bg-gray-200"
                style={{ backgroundColor: '#e5e7eb' }}
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default TeacherDashboard;