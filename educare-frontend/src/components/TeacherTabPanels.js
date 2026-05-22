import React from 'react';

export function OverviewTab({
  totalStudents,
  quizzes,
  pendingMaterials,
  masteryOverview,
  getMasteryBarColor,
  onGenerateBatch,
  batchProgress,
  batchSummary,
  setBatchSummary
}) {
  const avgPending = pendingMaterials.length;
  const [selectedBatchDifficulty, setSelectedBatchDifficulty] = React.useState('medium');

  const weakItemsCount = React.useMemo(() => {
    const seen = new Set();
    let count = 0;
    masteryOverview.forEach(topic => {
      if (topic.struggling_students && topic.struggling_students.length > 0) {
        topic.struggling_students.forEach(student => {
          const key = `${student.student_id}_${topic.topic_id}`;
          if (!seen.has(key)) {
            seen.add(key);
            count++;
          }
        });
      }
    });
    return count;
  }, [masteryOverview]);

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-xl font-bold mb-4">Class Overview</h2>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mb-4">
          {[
            { label: 'Students', val: totalStudents, color: '#2563eb' },
            { label: 'Quizzes', val: quizzes.length, color: '#7c3aed' },
            { label: 'Pending Approvals', val: avgPending, color: '#f59e0b' },
            { label: 'Topics Tracked', val: masteryOverview.length, color: '#14b8a6' },
          ].map((c) => (
            <div key={c.label} className="bg-white rounded-lg shadow-sm p-4 border border-gray-100">
              <div className="text-2xl font-bold" style={{ color: c.color }}>{c.val}</div>
              <div className="text-xs text-gray-500">{c.label}</div>
            </div>
          ))}
        </div>
      </div>

      {/* AI Smart Batch Gap Assistant Card */}
      <div className="bg-gradient-to-r from-slate-900 via-slate-800 to-indigo-950 p-6 rounded-2xl border border-slate-700/50 shadow-lg text-white mb-6 relative overflow-hidden">
        {/* Subtle background glow */}
        <div className="absolute top-0 right-0 w-80 h-80 bg-blue-500/10 rounded-full blur-3xl pointer-events-none" />
        <div className="absolute bottom-0 left-0 w-80 h-80 bg-indigo-500/10 rounded-full blur-3xl pointer-events-none" />

        <div className="relative z-10">
          <div className="flex items-start justify-between flex-wrap gap-4 mb-3">
            <div>
              <span className="text-xs px-2.5 py-1 rounded-full font-bold bg-blue-500/20 text-blue-300 border border-blue-400/20 shadow-inner flex items-center gap-1.5 w-fit mb-2">
                ⚡ AI Smart Assistant
              </span>
              <h3 className="text-xl font-extrabold text-white flex items-center gap-2">
                Learning Gap Batch Handout Generator
              </h3>
            </div>
            <div className="bg-white/10 px-4 py-2 rounded-xl border border-white/10 text-right min-w-[120px]">
              <div className="text-2xl font-black text-amber-400">{weakItemsCount}</div>
              <div className="text-[10px] text-slate-300 uppercase tracking-wider font-bold">Unresolved Gaps</div>
            </div>
          </div>

          <p className="text-sm text-slate-300 max-w-3xl mb-5 leading-relaxed">
            Auto-detect student weaknesses from recent quiz results (scores under 70%) and instantly compile customized, RAG-backed handouts to fill each learning gap.
          </p>

          {!batchProgress && !batchSummary && (
            <div className="flex items-center gap-3 flex-wrap">
              <div className="flex items-center gap-2 bg-white/5 border border-white/10 rounded-xl px-3 py-2">
                <label htmlFor="batch-difficulty" className="text-xs font-semibold text-slate-400">Sheet Difficulty:</label>
                <select
                  id="batch-difficulty"
                  value={selectedBatchDifficulty}
                  onChange={(e) => setSelectedBatchDifficulty(e.target.value)}
                  className="bg-slate-800 border border-slate-700 rounded-lg text-xs font-bold text-white focus:outline-none focus:ring-1 focus:ring-blue-500 px-2 py-1 shadow-sm"
                >
                  <option value="easy">🟢 Easy Practice</option>
                  <option value="medium">🟡 Medium Standard</option>
                  <option value="hard">🔴 Advanced Practice</option>
                </select>
              </div>

              <button
                type="button"
                onClick={() => onGenerateBatch(selectedBatchDifficulty)}
                disabled={weakItemsCount === 0}
                className={`px-6 py-3 rounded-xl text-sm font-bold text-white shadow-md transition-all active:scale-[0.98] flex items-center gap-2 cursor-pointer ${
                  weakItemsCount === 0
                    ? 'bg-slate-700 text-slate-500 border border-slate-850 cursor-not-allowed'
                    : 'bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-700 hover:to-indigo-700 border border-blue-500/30'
                }`}
              >
                🪄 Generate Materials for All Struggling Students
              </button>
            </div>
          )}

          {/* Active Generation Progress Bar */}
          {batchProgress && (
            <div className="bg-slate-800/80 p-4 rounded-xl border border-slate-700/60 shadow-inner animate-pulse">
              <div className="flex justify-between items-center mb-2">
                <span className="text-xs font-bold text-blue-400 flex items-center gap-2">
                  <svg className="animate-spin h-3.5 w-3.5 text-blue-400" fill="none" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                  </svg>
                  Generating Handout {batchProgress.current} of {batchProgress.total}...
                </span>
                <span className="text-xs font-black text-slate-300">
                  {Math.round((batchProgress.current / batchProgress.total) * 100)}%
                </span>
              </div>

              {/* Progress track */}
              <div className="w-full bg-slate-950 h-3.5 rounded-full overflow-hidden mb-2 border border-slate-900 shadow-inner">
                <div
                  className="bg-gradient-to-r from-blue-500 via-indigo-500 to-emerald-500 h-3.5 rounded-full transition-all duration-300"
                  style={{ width: `${(batchProgress.current / batchProgress.total) * 100}%` }}
                />
              </div>

              <div className="flex justify-between text-[11px] text-slate-400">
                <span>Student: <strong className="text-white">{batchProgress.currentStudent || 'Compiling...'}</strong></span>
                <span>Weakness: <strong className="text-yellow-400">{batchProgress.currentTopic || 'Evaluating...'}</strong></span>
              </div>
            </div>
          )}

          {/* Dynamic completion summary inside the panel */}
          {batchSummary && (
            <div className="bg-slate-800/80 p-5 rounded-xl border border-slate-700/60 shadow-inner text-sm space-y-4">
              <div className="flex items-center justify-between border-b border-slate-700/50 pb-2">
                <h4 className="font-extrabold text-emerald-400 flex items-center gap-1.5 text-base">
                  🎉 Batch Material Generation Completed!
                </h4>
                <button
                  onClick={() => setBatchSummary(null)}
                  className="text-xs bg-slate-700 hover:bg-slate-600 px-2.5 py-1 rounded-lg text-slate-200 transition cursor-pointer"
                >
                  Clear Results
                </button>
              </div>

              <div className="grid grid-cols-2 sm:grid-cols-3 gap-2 text-center text-xs">
                <div className="bg-slate-900 p-2.5 rounded-lg border border-slate-800 shadow-inner">
                  <div className="text-emerald-400 font-black text-base">{batchSummary.generated.length}</div>
                  <div className="text-[10px] text-slate-400 uppercase font-semibold">Compiled</div>
                </div>
                <div className="bg-slate-900 p-2.5 rounded-lg border border-slate-800 shadow-inner">
                  <div className="text-amber-400 font-black text-base">{batchSummary.failed.filter(f => f.status === 'duplicate').length}</div>
                  <div className="text-[10px] text-slate-400 uppercase font-semibold">Skipped (Duplicate)</div>
                </div>
                <div className="bg-slate-900 p-2.5 rounded-lg border border-slate-800 shadow-inner col-span-2 sm:col-span-1">
                  <div className="text-rose-400 font-black text-base">{batchSummary.failed.filter(f => f.status === 'failed').length}</div>
                  <div className="text-[10px] text-slate-400 uppercase font-semibold">Failed</div>
                </div>
              </div>

              <div className="space-y-1.5 pt-2 border-t border-slate-700/50">
                <p className="text-xs font-bold text-slate-300 uppercase tracking-wide mb-2">Detailed Generation Log:</p>
                <div className="space-y-1 max-h-[150px] overflow-y-auto pr-1">
                  {batchSummary.generated.map((item, idx) => (
                    <div key={`s-${idx}`} className="flex justify-between items-center text-xs text-slate-300 py-1 border-b border-slate-800/40">
                      <span className="truncate max-w-[250px]">🟢 <strong>{item.studentName}</strong>: {item.topicName}</span>
                      <span className="text-[10px] text-emerald-400 bg-emerald-500/10 px-2 py-0.5 rounded font-medium border border-emerald-500/20">Sheet Submitted</span>
                    </div>
                  ))}
                  {batchSummary.failed.map((item, idx) => (
                    <div key={`f-${idx}`} className="flex justify-between items-center text-xs text-slate-400 py-1 border-b border-slate-800/40">
                      <span className="truncate max-w-[250px]">
                        {item.status === 'duplicate' ? '🟡' : '🔴'} <strong>{item.studentName}</strong>: {item.topicName}
                      </span>
                      <span className={`text-[10px] px-2 py-0.5 rounded font-medium border ${
                        item.status === 'duplicate'
                          ? 'text-amber-300 bg-amber-500/10 border-amber-500/20'
                          : 'text-rose-300 bg-rose-500/10 border-rose-500/20'
                      }`}>
                        {item.status === 'duplicate' ? 'Recent Duplicate' : 'Failed'}
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          )}
        </div>
      </div>

      <div className="bg-white rounded-lg shadow-sm overflow-hidden">
        <table className="w-full text-sm">
          <thead className="bg-gray-50">
            <tr>
              <th className="text-left p-2">Topic</th>
              <th className="text-left p-2">Grade</th>
              <th className="text-left p-2">Mastery</th>
              <th className="text-left p-2">Struggling</th>
            </tr>
          </thead>
          <tbody>
            {masteryOverview.map((t) => (
              <tr key={t.topic_id} className="border-t">
                <td className="p-2 font-medium">{t.topic_name}</td>
                <td className="p-2 text-gray-500">Grade {t.grade_level}</td>
                <td className="p-2">
                  <div className="flex items-center gap-2">
                    <div className="flex-1 bg-gray-200 rounded-full h-2 max-w-[120px]">
                      <div className={`h-2 rounded-full ${getMasteryBarColor(t.mastery_pct)}`} style={{ width: `${t.mastery_pct}%` }} />
                    </div>
                    <span className="text-xs">{t.mastery_pct}%</span>
                  </div>
                </td>
                <td className="p-2 text-red-600 text-xs">{t.struggling_students?.length || 0}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

export function MasteryTab({ masteryOverview, expandedTopic, setExpandedTopic, getMasteryBarColor }) {
  return (
    <div>
      <h2 className="text-xl font-bold mb-4">Mastery Tracker</h2>
      <div className="space-y-2">
        {masteryOverview.map((topic) => (
          <div key={topic.topic_id} className="bg-white rounded-lg shadow-sm border border-gray-100 overflow-hidden">
            <button
              type="button"
              className="w-full flex items-center justify-between p-3 text-left hover:bg-gray-50"
              onClick={() => setExpandedTopic(expandedTopic === topic.topic_id ? null : topic.topic_id)}
            >
              <div>
                <span className="font-medium text-sm">{topic.topic_name}</span>
                <span className="text-xs text-gray-500 ml-2">Grade {topic.grade_level}</span>
              </div>
              <span className="text-sm font-semibold" style={{ color: topic.mastery_pct >= 70 ? '#10b981' : '#f59e0b' }}>
                {topic.mastery_pct}% mastered
              </span>
            </button>
            {expandedTopic === topic.topic_id && (
              <div className="px-3 pb-3 border-t border-gray-100 text-sm space-y-2">
                {topic.struggling_students?.length > 0 && (
                  <div>
                    <p className="text-xs font-semibold text-red-700 mb-1">Struggling</p>
                    {topic.struggling_students.map((s) => (
                      <div key={s.student_id} className="flex justify-between py-1 text-xs">
                        <span>{s.full_name}</span>
                        <span>{s.avg_score}%</span>
                      </div>
                    ))}
                  </div>
                )}
                {topic.blocked_students?.length > 0 && (
                  <div>
                    <p className="text-xs font-semibold text-gray-600 mb-1">Blocked (prerequisites)</p>
                    {topic.blocked_students.map((s) => (
                      <div key={s.student_id} className="text-xs text-gray-500">{s.full_name}</div>
                    ))}
                  </div>
                )}
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}

export function CurriculumTab({
  curriculumQuery,
  setCurriculumQuery,
  curriculumLoading,
  curriculumSearched,
  handleCurriculumSearch,
  curriculumResults,
  onGenerateFromSearch,
  generatingIds
}) {
  const [expandedIndices, setExpandedIndices] = React.useState({});
  const [selectedDifficulties, setSelectedDifficulties] = React.useState({});

  const toggleExpand = (index) => {
    setExpandedIndices(prev => ({ ...prev, [index]: !prev[index] }));
  };

  const handleDifficultyChange = (index, value) => {
    setSelectedDifficulties(prev => ({ ...prev, [index]: value }));
  };

  const prettifySource = (source) => {
    if (!source) return 'Curriculum';
    return source.replace('.pdf', '').replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase());
  };

  return (
    <div className="space-y-6">
      <div className="bg-gradient-to-r from-blue-50 to-indigo-50 p-6 rounded-2xl border border-blue-100/50 shadow-sm">
        <h2 className="text-2xl font-bold text-gray-800 flex items-center gap-2 mb-2">
          🔍 Curriculum Explorer
        </h2>
        <p className="text-sm text-gray-600 mb-4">
          Search across all 6 high school curriculum reference books, examine standard outlines and examples, and auto-compile customized handouts instantly.
        </p>
        <form onSubmit={handleCurriculumSearch} className="flex gap-2">
          <div className="relative flex-1">
            <input
              type="text"
              value={curriculumQuery}
              onChange={(e) => setCurriculumQuery(e.target.value)}
              placeholder="Enter topics, formulas, or equations (e.g. quadratic formula, relations, systems of linear equations)..."
              className="w-full pl-4 pr-4 py-3 text-sm bg-white border border-gray-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all shadow-inner"
            />
          </div>
          <button
            type="submit"
            disabled={curriculumLoading}
            className="px-6 py-3 text-sm font-semibold text-white rounded-xl shadow-md hover:shadow-lg active:scale-95 transition-all flex items-center gap-2"
            style={{ backgroundColor: '#2563eb' }}
          >
            {curriculumLoading ? (
              <>
                <svg className="animate-spin h-4 w-4 text-white" fill="none" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                </svg>
                Searching...
              </>
            ) : 'Search'}
          </button>
        </form>
      </div>

      {curriculumSearched && (
        <div className="flex justify-between items-center px-1">
          <span className="text-sm font-medium text-gray-500">
            {curriculumResults.length === 0 ? 'No matching references found.' : `Found ${curriculumResults.length} matching curriculum reference${curriculumResults.length > 1 ? 's' : ''}.`}
          </span>
        </div>
      )}

      <div className="space-y-4">
        {curriculumResults.map((r, i) => {
          const isExpanded = !!expandedIndices[i];
          const isGenerating = !!generatingIds[i];
          const selectedDiff = selectedDifficulties[i] || 'medium';
          
          const maxSnippetLen = 350;
          const needsTruncation = r.text && r.text.length > maxSnippetLen;
          const displayedText = isExpanded || !needsTruncation ? r.text : `${r.text.substring(0, maxSnippetLen)}...`;

          return (
            <div
              key={i}
              className="bg-white p-5 rounded-2xl border border-gray-100 shadow-sm hover:shadow-md transition-all duration-300 flex flex-col justify-between relative overflow-hidden"
              style={{ borderLeft: '4px solid #2563eb' }}
            >
              {isGenerating && (
                <div className="absolute inset-0 bg-blue-50/80 backdrop-blur-[1px] flex flex-col items-center justify-center z-10 transition-opacity">
                  <div className="flex items-center gap-3">
                    <svg className="animate-spin h-6 w-6 text-blue-600" fill="none" viewBox="0 0 24 24">
                      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                    </svg>
                    <span className="text-sm font-bold text-blue-700 animate-pulse">Compiling practice materials...</span>
                  </div>
                </div>
              )}

              <div>
                <div className="flex gap-2 flex-wrap items-center mb-3">
                  <span className="text-xs px-2.5 py-1 rounded-lg font-semibold bg-emerald-50 text-emerald-700 border border-emerald-100 shadow-sm">
                    📚 {prettifySource(r.source_file || r.source)}
                  </span>
                  {r.source_grade && (
                    <span className="text-xs px-2.5 py-1 rounded-lg font-semibold bg-purple-50 text-purple-700 border border-purple-100 shadow-sm">
                      🎓 Grade {r.source_grade}
                    </span>
                  )}
                  <span className="text-xs px-2 py-1 rounded-lg font-medium bg-gray-50 text-gray-500 border border-gray-200">
                    Page {r.source_page || r.page || '?'}
                  </span>
                  {r.similarity != null && (
                    <span className="text-xs px-2 py-1 rounded-lg font-bold bg-blue-50 text-blue-600 border border-blue-100 shadow-sm ml-auto">
                      🎯 {r.similarity}% match
                    </span>
                  )}
                </div>

                {r.section && (
                  <h4 className="text-sm font-bold text-gray-800 mb-2 border-b border-gray-50 pb-1 flex items-center gap-1.5">
                    💡 <span className="text-indigo-600">{r.section}</span>
                  </h4>
                )}

                <div className="bg-gray-50/50 p-3.5 rounded-xl border border-gray-100/50 mb-4">
                  <p className="text-gray-700 text-xs leading-relaxed whitespace-pre-line font-normal">{displayedText}</p>
                  
                  {needsTruncation && (
                    <button
                      onClick={() => toggleExpand(i)}
                      className="text-xs font-bold text-blue-600 hover:text-blue-700 transition mt-2 flex items-center gap-1 focus:outline-none"
                    >
                      {isExpanded ? 'Collapse ↑' : 'Show Full Chunk ↓'}
                    </button>
                  )}
                </div>
              </div>

              <div className="flex items-center gap-3 pt-3 border-t border-gray-100 mt-auto flex-wrap justify-between">
                <div className="flex items-center gap-2">
                  <label htmlFor={`diff-${i}`} className="text-xs font-semibold text-gray-500">Difficulty:</label>
                  <select
                    id={`diff-${i}`}
                    value={selectedDiff}
                    disabled={isGenerating}
                    onChange={(e) => handleDifficultyChange(i, e.target.value)}
                    className="text-xs font-semibold bg-white border border-gray-200 rounded-lg px-2 py-1.5 focus:outline-none focus:ring-1 focus:ring-blue-500 text-gray-700 shadow-sm"
                  >
                    <option value="easy">🟢 Easy</option>
                    <option value="medium">🟡 Medium</option>
                    <option value="hard">🔴 Hard</option>
                  </select>
                </div>

                <button
                  type="button"
                  disabled={isGenerating}
                  onClick={() => onGenerateFromSearch(r, i, selectedDiff)}
                  className="px-4 py-2 rounded-xl text-xs font-bold text-white shadow-sm hover:shadow-md transition flex items-center gap-1.5 active:scale-95 cursor-pointer"
                  style={{ backgroundColor: '#2563eb' }}
                >
                  🪄 Generate Material from This Result
                </button>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}

export function HeatmapTab({ heatmapData, heatmapGradeFilter, setHeatmapGradeFilter, heatmapSort, setHeatmapSort, setSelectedHeatmapTopic }) {
  const filtered = heatmapData
    .filter((t) => heatmapGradeFilter === 'all' || String(t.grade_level) === heatmapGradeFilter)
    .sort((a, b) => {
      if (heatmapSort === 'mastery') {
        const pct = (t) => t.mastery_percentage ?? t.mastery_pct ?? 0;
        return pct(b) - pct(a);
      }
      return (a.topic_name || '').localeCompare(b.topic_name || '');
    });

  const statusColor = (s) => (s === 'good' ? '#10b981' : s === 'needs_attention' ? '#f59e0b' : '#ef4444');

  return (
    <div>
      <h2 className="text-xl font-bold mb-4">Gap Heatmap</h2>
      <div className="flex gap-3 mb-4">
        <select value={heatmapGradeFilter} onChange={(e) => setHeatmapGradeFilter(e.target.value)} className="text-sm border rounded px-2 py-1">
          <option value="all">All Grades</option>
          {[9, 10, 11, 12].map((g) => <option key={g} value={String(g)}>Grade {g}</option>)}
        </select>
        <select value={heatmapSort} onChange={(e) => setHeatmapSort(e.target.value)} className="text-sm border rounded px-2 py-1">
          <option value="mastery">Sort by Mastery</option>
          <option value="name">Sort by Name</option>
        </select>
      </div>
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-2">
        {filtered.map((t) => (
          <button
            key={t.topic_id}
            type="button"
            onClick={() => setSelectedHeatmapTopic(t)}
            className="p-3 rounded-lg text-left text-white text-sm hover:opacity-90 transition"
            style={{ backgroundColor: statusColor(t.status) }}
          >
            <div className="font-medium truncate">{t.topic_name}</div>
            <div className="text-xs opacity-90">G{t.grade_level} · {t.mastery_percentage ?? t.mastery_pct ?? 0}%</div>
          </button>
        ))}
      </div>
    </div>
  );
}

export function StudentsTab({
  students,
  selectedStudent,
  handleStudentSelect,
  studentGaps,
  generateTopic,
  setGenerateTopic,
  generateDifficulty,
  setGenerateDifficulty,
  isGenerating,
  generateStatus,
  handleGenerateMaterial,
  handleGenerateForWeakness,
  getWeaknessColor,
}) {
  return (
    <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
      <div className="lg:col-span-1 bg-white rounded-lg shadow-sm p-3 max-h-[70vh] overflow-y-auto">
        <h3 className="text-sm font-semibold mb-2">Students</h3>
        {students.map((s) => (
          <button
            key={s.user_id}
            type="button"
            onClick={() => handleStudentSelect(s)}
            className={`w-full text-left p-2 rounded mb-1 text-sm ${
              selectedStudent?.user_id === s.user_id ? 'bg-blue-50 border border-blue-200' : 'hover:bg-gray-50'
            }`}
          >
            <div className="font-medium">{s.full_name}</div>
            <div className="text-xs text-gray-500">Grade {s.grade_level} · {s.section}</div>
          </button>
        ))}
      </div>
      <div className="lg:col-span-2">
        {selectedStudent ? (
          <div className="bg-white rounded-lg shadow-sm p-4">
            <h3 className="font-bold mb-1">{selectedStudent.full_name}</h3>
            <p className="text-xs text-gray-500 mb-4">Weak topics from quiz results</p>
            {studentGaps.length === 0 ? (
              <p className="text-sm text-gray-600">
                No learning gaps detected yet. Gaps appear after the student completes quizzes and scores below 70% on a topic.
              </p>
            ) : (
              <div className="space-y-2 mb-4">
                {studentGaps.map((g) => (
                  <div key={g.topic_id} className="flex items-center justify-between p-2 border rounded-lg">
                    <div>
                      <span className="text-sm font-medium">{g.topic_name}</span>
                      <span className={`ml-2 px-2 py-0.5 rounded text-xs ${getWeaknessColor(g.weakness_level)}`}>
                        {g.weakness_level}
                      </span>
                      <span className="text-xs text-gray-500 ml-2">{g.avg_score}% avg</span>
                    </div>
                    <button
                      type="button"
                      onClick={() => handleGenerateForWeakness(g)}
                      disabled={isGenerating}
                      className="px-3 py-1 text-xs text-white rounded-md disabled:opacity-50"
                      style={{ backgroundColor: '#14b8a6' }}
                    >
                      Generate for Weakness
                    </button>
                  </div>
                ))}
              </div>
            )}
            <div className="border-t pt-3">
              <p className="text-xs text-gray-500 mb-2">Custom topic generation</p>
              <input
                type="text"
                value={generateTopic}
                onChange={(e) => setGenerateTopic(e.target.value)}
                placeholder="Topic name..."
                className="w-full px-2 py-1.5 text-sm border rounded mb-2"
              />
              <select value={generateDifficulty} onChange={(e) => setGenerateDifficulty(e.target.value)} className="text-sm border rounded px-2 py-1 mb-2">
                <option value="easy">Easy</option>
                <option value="medium">Medium</option>
                <option value="hard">Hard</option>
              </select>
              <button
                type="button"
                onClick={handleGenerateMaterial}
                disabled={isGenerating || !generateTopic}
                className="px-4 py-1.5 text-sm text-white rounded-md disabled:opacity-50"
                style={{ backgroundColor: '#2563eb' }}
              >
                {isGenerating ? 'Generating…' : 'Generate Material'}
              </button>
              {generateStatus === 'success' && <p className="text-xs text-green-600 mt-2">Sent for approval.</p>}
              {generateStatus === 'error' && <p className="text-xs text-red-600 mt-2">Generation failed or duplicate (7-day limit).</p>}
            </div>
          </div>
        ) : (
          <p className="text-sm text-gray-500">Select a student to view gaps and generate materials.</p>
        )}
      </div>
    </div>
  );
}

export function QuizzesTab({ quizzes, setShowCreateQuiz, setShowAIQuizModal, setAiQuizError, setAiQuizResult, handleOpenTopicGenerator, handleViewQuizResults, handleEditQuiz, handleDeleteQuiz }) {
  return (
    <div>
      <div className="flex flex-wrap gap-2 mb-4">
        <button type="button" onClick={() => setShowCreateQuiz(true)} className="px-3 py-1.5 text-sm text-white rounded-md" style={{ backgroundColor: '#2563eb' }}>
          + Create New Quiz
        </button>
        <button
          type="button"
          onClick={() => { setShowAIQuizModal(true); setAiQuizError(''); setAiQuizResult(null); }}
          className="px-3 py-1.5 text-sm text-white rounded-md"
          style={{ backgroundColor: '#7c3aed' }}
        >
          ✦ Generate AI Quiz
        </button>
        <button type="button" onClick={handleOpenTopicGenerator} className="px-3 py-1.5 text-sm text-white rounded-md" style={{ backgroundColor: '#059669' }}>
          Generate Material by Topic
        </button>
      </div>
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
        {quizzes.map((quiz) => (
          <div key={quiz.quiz_id} className="bg-white rounded-lg shadow-sm p-4 border border-gray-100">
            <h3 className="font-semibold text-sm">{quiz.title}</h3>
            <p className="text-xs text-gray-500 mt-1">{quiz.topic_name} · Grade {quiz.grade_level}</p>
            <p className="text-xs text-gray-400">{quiz.total_marks} marks · {quiz.time_limit} min</p>
            <div className="flex gap-2 mt-3 flex-wrap">
              <button type="button" onClick={() => handleViewQuizResults(quiz)} className="text-xs text-blue-600 hover:underline">Results</button>
              <button type="button" onClick={() => handleEditQuiz(quiz)} className="text-xs text-gray-600 hover:underline">Edit</button>
              <button type="button" onClick={() => handleDeleteQuiz(quiz.quiz_id)} className="text-xs text-red-600 hover:underline">Delete</button>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

export function ApprovalsTab({ pendingMaterials, handleApproveMaterial, setShowRejectConfirm }) {
  const [expandedMaterialIds, setExpandedMaterialIds] = React.useState({});

  const toggleExpand = (materialId) => {
    setExpandedMaterialIds(prev => ({
      ...prev,
      [materialId]: !prev[materialId]
    }));
  };

  const isHtml = (str) => {
    return /<[a-z][\s\S]*>/i.test(str || '');
  };

  const parseQuestions = (html) => {
    if (!html) return [];
    try {
      const parser = new DOMParser();
      const doc = parser.parseFromString(html, 'text/html');
      const qDivs = doc.querySelectorAll('.rag-question');
      return Array.from(qDivs).map((div, i) => {
        const correctIdx = parseInt(div.getAttribute('data-correct') || '0');
        const questionText = div.querySelector('p')?.textContent || '';
        const options = Array.from(div.querySelectorAll('.rag-option')).map((li) => li.textContent);
        const explanation = div.querySelector('.rag-answer')?.textContent || '';
        return { idx: i, questionText, options, correctIdx, explanation };
      });
    } catch (e) {
      console.error(e);
      return [];
    }
  };

  const getContextHtml = (html) => {
    if (!html) return '';
    try {
      const parser = new DOMParser();
      const doc = parser.parseFromString(html, 'text/html');
      doc.querySelectorAll('.rag-questions').forEach((el) => el.remove());
      return doc.body.innerHTML;
    } catch (e) {
      console.error(e);
      return html;
    }
  };

  const formatDate = (dateStr) => {
    if (!dateStr) return '';
    try {
      const d = new Date(dateStr);
      if (isNaN(d.getTime())) return dateStr;
      return d.toLocaleDateString(undefined, { year: 'numeric', month: 'short', day: 'numeric' });
    } catch (e) {
      return dateStr;
    }
  };

  return (
    <div>
      <h2 className="text-xl font-bold mb-4">Pending Approvals ({pendingMaterials.length})</h2>
      {pendingMaterials.length === 0 ? (
        <p className="text-sm text-gray-500 bg-white p-6 rounded-lg border border-gray-100 text-center">No materials awaiting approval.</p>
      ) : (
        <div className="space-y-4">
          {pendingMaterials.map((m) => {
            const isExpanded = !!expandedMaterialIds[m.material_id];
            const hasHtml = isHtml(m.content);
            const questions = hasHtml ? parseQuestions(m.content) : [];
            const contextHtml = hasHtml ? getContextHtml(m.content) : '';

            return (
              <div
                key={m.material_id}
                className="bg-white rounded-lg shadow-sm border border-gray-200 overflow-hidden hover:shadow-md transition-all duration-200"
              >
                {/* Header Section */}
                <div className="p-4 bg-white">
                  <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-3">
                    <div className="flex-1 min-w-0">
                      <h3 className="text-base font-bold text-gray-900 leading-snug">{m.title}</h3>
                      <div className="flex flex-wrap items-center gap-2 mt-2 text-xs text-gray-500">
                        {m.topic_name && (
                          <span className="px-2 py-0.5 rounded-full font-semibold flex items-center bg-blue-50 text-blue-700">
                            <svg className="w-3 h-3 mr-1 flex-shrink-0" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24">
                              <path strokeLinecap="round" strokeLinejoin="round" d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" />
                            </svg>
                            {m.topic_name}
                          </span>
                        )}
                        {m.generated_date && (
                          <span className="flex items-center">
                            <svg className="w-3 h-3 mr-1 text-gray-400 flex-shrink-0" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24">
                              <path strokeLinecap="round" strokeLinejoin="round" d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
                            </svg>
                            {formatDate(m.generated_date)}
                          </span>
                        )}
                        {m.source_citation && (
                          <span className="flex items-center italic text-gray-400 truncate max-w-[250px]" title={m.source_citation}>
                            <svg className="w-3 h-3 mr-1 text-gray-400 flex-shrink-0" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24">
                              <path strokeLinecap="round" strokeLinejoin="round" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                            </svg>
                            {m.source_citation}
                          </span>
                        )}
                      </div>
                    </div>
                    
                    {/* Action Buttons */}
                    <div className="flex items-center gap-2 flex-shrink-0 mt-3 md:mt-0 w-full md:w-auto justify-between md:justify-end">
                      <button
                        type="button"
                        onClick={() => toggleExpand(m.material_id)}
                        className="px-3 py-1.5 text-xs font-semibold rounded-md border border-gray-300 text-gray-700 bg-gray-50 hover:bg-gray-100 transition flex items-center gap-1"
                      >
                        {isExpanded ? (
                          <>
                            Hide Details
                            <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 15l7-7 7 7" />
                            </svg>
                          </>
                        ) : (
                          <>
                            View Details
                            <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                            </svg>
                          </>
                        )}
                      </button>
                      
                      <div className="flex items-center gap-2">
                        <button
                          type="button"
                          onClick={() => handleApproveMaterial(m.material_id)}
                          className="px-3 py-1.5 text-xs font-bold text-white rounded-md shadow-sm hover:opacity-95 transition"
                          style={{ backgroundColor: '#14b8a6' }}
                        >
                          Approve
                        </button>
                        
                        <button
                          type="button"
                          onClick={() => setShowRejectConfirm(m.material_id)}
                          className="px-3 py-1.5 text-xs font-bold text-white rounded-md shadow-sm hover:opacity-95 transition"
                          style={{ backgroundColor: '#ef4444' }}
                        >
                          Reject
                        </button>
                      </div>
                    </div>
                  </div>
                </div>

                {/* Expanded Details Section */}
                {isExpanded && (
                  <div className="bg-gray-50 border-t border-gray-100">
                    <div className="p-4 space-y-4">
                      {/* Full Content (Explanation, Examples, Formulas) */}
                      <div className="bg-white rounded-lg p-4 border border-gray-100 shadow-xs">
                        <h4 className="text-xs font-bold text-gray-400 uppercase tracking-wider mb-2">Curriculum Context & Explanation</h4>
                        {hasHtml ? (
                          <div
                            className="text-sm text-gray-700 leading-relaxed font-sans whitespace-pre-wrap rag-content"
                            dangerouslySetInnerHTML={{ __html: contextHtml }}
                          />
                        ) : (
                          <div className="text-sm text-gray-700 leading-relaxed font-sans whitespace-pre-wrap">
                            {m.content}
                          </div>
                        )}
                      </div>

                      {/* Practice Questions Section */}
                      {hasHtml && questions.length > 0 && (
                        <div className="space-y-3">
                          <h4 className="text-xs font-bold text-gray-400 uppercase tracking-wider">Practice Questions ({questions.length})</h4>
                          <div className="grid grid-cols-1 gap-3">
                            {questions.map((q) => (
                              <div key={q.idx} className="bg-white rounded-lg p-4 border border-gray-100 shadow-xs">
                                <p className="text-sm font-semibold text-gray-800 mb-2">
                                  Q{q.idx + 1}. {q.questionText}
                                </p>
                                <ul className="space-y-1.5 mb-3">
                                  {q.options.map((opt, oIdx) => {
                                    const isCorrect = oIdx === q.correctIdx;
                                    return (
                                      <li
                                        key={oIdx}
                                        className={`text-xs px-3 py-2 rounded-md transition-all ${
                                          isCorrect
                                            ? 'bg-emerald-50 border border-emerald-200 text-emerald-800 font-semibold'
                                            : 'bg-gray-50 border border-gray-100 text-gray-600'
                                        }`}
                                      >
                                        <span className="font-bold mr-1.5">{String.fromCharCode(65 + oIdx)}.</span>
                                        {opt}
                                        {isCorrect && (
                                          <span className="ml-2 text-[9px] px-1.5 py-0.5 rounded bg-emerald-100 text-emerald-700 font-bold uppercase tracking-wider">
                                            Correct Answer
                                          </span>
                                        )}
                                      </li>
                                    );
                                  })}
                                </ul>
                                {q.explanation && (
                                  <div className="bg-blue-50 border border-blue-100 rounded-md p-3 text-xs text-blue-800">
                                    <span className="font-bold block mb-1">Explanation:</span>
                                    {q.explanation}
                                  </div>
                                )}
                              </div>
                            ))}
                          </div>
                        </div>
                      )}
                      
                      {/* Expanded Section Footer Actions */}
                      <div className="flex justify-end items-center gap-2 pt-3 border-t border-gray-200">
                        <button
                          type="button"
                          onClick={() => toggleExpand(m.material_id)}
                          className="px-3 py-1.5 text-xs font-semibold text-gray-500 hover:text-gray-700 transition"
                        >
                          Collapse Details
                        </button>
                        <button
                          type="button"
                          onClick={() => handleApproveMaterial(m.material_id)}
                          className="px-4 py-1.5 text-xs font-bold text-white rounded-md shadow-sm hover:opacity-95 transition"
                          style={{ backgroundColor: '#14b8a6' }}
                        >
                          Approve Material
                        </button>
                        <button
                          type="button"
                          onClick={() => setShowRejectConfirm(m.material_id)}
                          className="px-4 py-1.5 text-xs font-bold text-white rounded-md shadow-sm hover:opacity-95 transition"
                          style={{ backgroundColor: '#ef4444' }}
                        >
                          Reject Material
                        </button>
                      </div>
                    </div>
                  </div>
                )}
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
