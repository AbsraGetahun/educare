import React, { useState, useEffect, useCallback } from 'react';
import {
  postPeerQuestion,
  getPeerQuestionFeed,
  getMyPeerQuestions,
  postPeerAnswer,
} from '../services/api';
import FilePicker from './FilePicker';
import AttachmentList from './AttachmentList';

function PeerHelpBoard({ studentId, fullName }) {
  const [feed, setFeed] = useState([]);
  const [myQuestions, setMyQuestions] = useState([]);
  const [newQuestion, setNewQuestion] = useState('');
  const [questionFiles, setQuestionFiles] = useState([]);
  const [answerDrafts, setAnswerDrafts] = useState({});
  const [answerFiles, setAnswerFiles] = useState({});
  const [answeringId, setAnsweringId] = useState(null);
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [view, setView] = useState('feed');

  const loadData = useCallback(async () => {
    if (!studentId) return;
    try {
      const [feedData, mineData] = await Promise.all([
        getPeerQuestionFeed(studentId),
        getMyPeerQuestions(studentId),
      ]);
      setFeed(feedData.questions || []);
      setMyQuestions(mineData.questions || []);
      setError('');
    } catch (err) {
      setError(err.response?.data?.error || 'Failed to load peer questions');
    } finally {
      setLoading(false);
    }
  }, [studentId]);

  useEffect(() => {
    loadData();
    const interval = setInterval(loadData, 20000);
    return () => clearInterval(interval);
  }, [loadData]);

  const handlePostQuestion = async (e) => {
    e.preventDefault();
    const text = newQuestion.trim();
    if ((!text || text.length < 5) && questionFiles.length === 0) return;
    if (submitting) return;
    setSubmitting(true);
    setError('');
    setSuccess('');
    try {
      await postPeerQuestion(studentId, text, questionFiles);
      setNewQuestion('');
      setQuestionFiles([]);
      setSuccess('Your question was posted — all students can see it.');
      await loadData();
      setView('feed');
    } catch (err) {
      setError(err.response?.data?.error || 'Could not post question');
    } finally {
      setSubmitting(false);
    }
  };

  const handlePostAnswer = async (questionId) => {
    const text = (answerDrafts[questionId] || '').trim();
    const files = answerFiles[questionId] || [];
    if ((!text || text.length < 3) && files.length === 0) return;
    if (submitting) return;
    setSubmitting(true);
    setError('');
    setSuccess('');
    try {
      const res = await postPeerAnswer(questionId, studentId, text, files);
      setAnswerDrafts((prev) => ({ ...prev, [questionId]: '' }));
      setAnswerFiles((prev) => ({ ...prev, [questionId]: [] }));
      setAnsweringId(null);
      setSuccess(res.message || 'Answer sent privately to the asker.');
      await loadData();
    } catch (err) {
      setError(err.response?.data?.error || 'Could not send answer');
    } finally {
      setSubmitting(false);
    }
  };

  const formatTime = (iso) => {
    if (!iso) return '';
    try {
      return new Date(iso).toLocaleString();
    } catch {
      return iso;
    }
  };

  if (!studentId) {
    return (
      <p className="text-sm text-gray-500">Sign in as a student to use peer help.</p>
    );
  }

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-xl font-bold text-gray-900 mb-1">Peer Math Help</h2>
        <p className="text-sm text-gray-500">
          Post a math question for <strong>all students</strong> to see. When someone helps you,
          their answer is sent <strong>only to you</strong> — not shown to everyone else.
        </p>
      </div>

      {error && (
        <div className="bg-red-50 border border-red-200 text-red-700 px-3 py-2 rounded-lg text-sm">
          {error}
        </div>
      )}
      {success && (
        <div className="bg-green-50 border border-green-200 text-green-800 px-3 py-2 rounded-lg text-sm">
          {success}
        </div>
      )}

      {/* Post question */}
      <form
        onSubmit={handlePostQuestion}
        className="bg-white rounded-lg border border-gray-200 p-4 shadow-sm"
      >
        <label className="block text-sm font-semibold text-gray-800 mb-2">
          Ask the community
        </label>
        <textarea
          value={newQuestion}
          onChange={(e) => setNewQuestion(e.target.value)}
          placeholder="e.g. How do I factor x² - 5x + 6?"
          rows={3}
          className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
          maxLength={2000}
        />
        <FilePicker
          context="peer"
          files={questionFiles}
          onChange={setQuestionFiles}
          label="Attach images or files from your device (visible to all students)"
        />
        <div className="flex justify-between items-center mt-2">
          <span className="text-xs text-gray-400">{newQuestion.length}/2000</span>
          <button
            type="submit"
            disabled={submitting || (newQuestion.trim().length < 5 && questionFiles.length === 0)}
            className="px-4 py-2 bg-[#2563eb] text-white text-sm font-medium rounded-lg hover:bg-blue-700 disabled:opacity-50"
          >
            {submitting ? 'Posting…' : 'Post question (visible to all)'}
          </button>
        </div>
      </form>

      {/* View toggle */}
      <div className="flex gap-2 border-b border-gray-200">
        <button
          type="button"
          onClick={() => setView('feed')}
          className={`px-4 py-2 text-sm font-medium border-b-2 -mb-px ${
            view === 'feed'
              ? 'text-[#2563eb] border-[#2563eb]'
              : 'text-gray-500 border-transparent'
          }`}
        >
          All students&apos; questions ({feed.length})
        </button>
        <button
          type="button"
          onClick={() => setView('mine')}
          className={`px-4 py-2 text-sm font-medium border-b-2 -mb-px ${
            view === 'mine'
              ? 'text-[#2563eb] border-[#2563eb]'
              : 'text-gray-500 border-transparent'
          }`}
        >
          My questions &amp; private answers ({myQuestions.length})
        </button>
      </div>

      {loading ? (
        <div className="flex items-center gap-2 text-sm text-gray-500 py-8">
          <div className="w-5 h-5 border-2 border-blue-600 border-t-transparent rounded-full animate-spin" />
          Loading…
        </div>
      ) : view === 'feed' ? (
        <div className="space-y-3">
          {feed.length === 0 ? (
            <p className="text-sm text-gray-500 py-6 text-center bg-white rounded-lg border border-dashed border-gray-300">
              No questions yet. Be the first to ask!
            </p>
          ) : (
            feed.map((q) => (
              <div
                key={q.question_id}
                className="bg-white rounded-lg border border-gray-200 p-4 shadow-sm"
              >
                <div className="flex justify-between items-start gap-2 mb-2">
                  <div>
                    <span className="text-xs font-semibold text-blue-700">
                      {q.is_mine ? 'You asked' : q.asker_name}
                    </span>
                    <span className="text-xs text-gray-400 ml-2">{formatTime(q.created_at)}</span>
                  </div>
                  {q.i_answered && !q.is_mine && (
                    <span className="text-[10px] px-2 py-0.5 rounded-full bg-green-100 text-green-700">
                      You answered
                    </span>
                  )}
                </div>
                <p className="text-sm text-gray-800 whitespace-pre-wrap">{q.question_text}</p>
                <AttachmentList attachments={q.attachments} />

                {!q.is_mine && (
                  <div className="mt-3 pt-3 border-t border-gray-100">
                    {answeringId === q.question_id ? (
                      <div>
                        <label className="text-xs font-medium text-gray-600 block mb-1">
                          Your answer (private — only {q.asker_name} will see this)
                        </label>
                        <textarea
                          value={answerDrafts[q.question_id] || ''}
                          onChange={(e) =>
                            setAnswerDrafts((prev) => ({
                              ...prev,
                              [q.question_id]: e.target.value,
                            }))
                          }
                          rows={3}
                          className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm"
                          placeholder="Explain your solution…"
                          maxLength={3000}
                        />
                        <FilePicker
                          context="peer"
                          files={answerFiles[q.question_id] || []}
                          onChange={(files) =>
                            setAnswerFiles((prev) => ({ ...prev, [q.question_id]: files }))
                          }
                          label="Attach images or files (private to the asker only)"
                        />
                        <div className="flex gap-2 mt-2">
                          <button
                            type="button"
                            onClick={() => handlePostAnswer(q.question_id)}
                            disabled={
                              submitting ||
                              ((answerDrafts[q.question_id] || '').trim().length < 3 &&
                                !(answerFiles[q.question_id] || []).length)
                            }
                            className="px-3 py-1.5 bg-emerald-600 text-white text-xs font-medium rounded-md hover:bg-emerald-700 disabled:opacity-50"
                          >
                            Send private answer
                          </button>
                          <button
                            type="button"
                            onClick={() => setAnsweringId(null)}
                            className="px-3 py-1.5 text-gray-600 text-xs hover:bg-gray-100 rounded-md"
                          >
                            Cancel
                          </button>
                        </div>
                      </div>
                    ) : (
                      <button
                        type="button"
                        onClick={() => setAnsweringId(q.question_id)}
                        disabled={q.i_answered}
                        className="text-sm text-[#2563eb] font-medium hover:underline disabled:text-gray-400 disabled:no-underline"
                      >
                        {q.i_answered ? 'Already answered' : 'Answer this question'}
                      </button>
                    )}
                  </div>
                )}

                {q.is_mine && (
                  <p className="mt-2 text-xs text-gray-500 italic">
                    Check &quot;My questions &amp; private answers&quot; to see replies — other
                    students cannot see them.
                  </p>
                )}
              </div>
            ))
          )}
        </div>
      ) : (
        <div className="space-y-3">
          {myQuestions.length === 0 ? (
            <p className="text-sm text-gray-500 py-6 text-center bg-white rounded-lg border border-dashed border-gray-300">
              You have not asked any questions yet.
            </p>
          ) : (
            myQuestions.map((q) => (
              <div
                key={q.question_id}
                className="bg-white rounded-lg border border-blue-200 p-4 shadow-sm"
              >
                <p className="text-xs text-gray-400 mb-1">{formatTime(q.created_at)}</p>
                <p className="text-sm font-medium text-gray-900 whitespace-pre-wrap mb-3">
                  {q.question_text}
                </p>
                <AttachmentList attachments={q.attachments} className="mb-3" />
                {q.answers && q.answers.length > 0 ? (
                  <div className="space-y-2">
                    <p className="text-xs font-semibold text-gray-600 uppercase tracking-wide">
                      Private answers ({q.answer_count})
                    </p>
                    {q.answers.map((a, idx) => (
                      <div
                        key={idx}
                        className="bg-emerald-50 border border-emerald-100 rounded-lg p-3"
                      >
                        <p className="text-xs font-semibold text-emerald-800 mb-1">
                          From {a.responder_name}
                          <span className="font-normal text-gray-500 ml-2">
                            {formatTime(a.created_at)}
                          </span>
                        </p>
                        <p className="text-sm text-gray-800 whitespace-pre-wrap">
                          {a.answer_text}
                        </p>
                        <AttachmentList attachments={a.attachments} />
                      </div>
                    ))}
                  </div>
                ) : (
                  <p className="text-xs text-gray-500 italic">
                    No answers yet — waiting for a classmate to help.
                  </p>
                )}
              </div>
            ))
          )}
        </div>
      )}

      <p className="text-xs text-gray-400 text-center">
        Logged in as {fullName || 'Student'} · Feed refreshes every 20 seconds
      </p>
    </div>
  );
}

export default PeerHelpBoard;
