import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { getQuizById, submitQuiz } from '../services/api';
import { resolveUploadUrl } from '../utils/uploadUrl';

function QuizTaking() {
  const { quizId } = useParams();
  const navigate = useNavigate();
  const [quiz, setQuiz] = useState(null);
  const [currentQuestion, setCurrentQuestion] = useState(0);
  const [answers, setAnswers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState('');
  const [result, setResult] = useState(null);

  useEffect(() => {
    const fetchQuiz = async () => {
      try {
        const data = await getQuizById(quizId);
        setQuiz(data);
        setAnswers(new Array(data.questions.length).fill(null));
      } catch (err) {
        setError('Failed to load quiz');
      } finally {
        setLoading(false);
      }
    };
    fetchQuiz();
  }, [quizId]);

  const handleAnswer = (answer) => {
    const newAnswers = [...answers];
    newAnswers[currentQuestion] = answer;
    setAnswers(newAnswers);
  };

  const handleNext = () => {
    if (currentQuestion < quiz.questions.length - 1) {
      setCurrentQuestion(currentQuestion + 1);
    }
  };

  const handlePrevious = () => {
    if (currentQuestion > 0) {
      setCurrentQuestion(currentQuestion - 1);
    }
  };

  const handleSubmit = async () => {
    if (answers.some(a => a === null)) {
      setError('Please answer all questions before submitting');
      return;
    }

    setSubmitting(true);
    setError('');
    try {
      const studentId = localStorage.getItem('user_id');
      const formattedAnswers = answers.map((answer, index) => ({
        question_id: quiz.questions[index].question_id,
        answer: answer
      }));
      const response = await submitQuiz(quizId, studentId, formattedAnswers);
      setResult(response);
    } catch (err) {
      setError(err.response?.data?.error || 'Failed to submit quiz. Please try again.');
      setSubmitting(false);
    }
  };

  if (loading) return <div className="min-h-screen flex items-center justify-center">Loading...</div>;
  if (error) return <div className="min-h-screen flex items-center justify-center text-red-500">{error}</div>;

  // Show results screen after submission
  if (result) {
    const mastery = result.mastery_update;
    return (
      <div className="min-h-screen bg-gray-100 py-8">
        <div className="container mx-auto max-w-2xl">
          <div className="bg-white rounded-lg shadow-md p-6">
            <h1 className="text-2xl font-bold text-center mb-6">Quiz Complete!</h1>

            {/* Score */}
            <div className="text-center mb-6">
              <div className="text-5xl font-bold text-blue-600 mb-2">
                {result.score}/{result.total_marks ?? result.total_possible}
              </div>
              <div className="text-lg text-gray-600">
                {Math.min(100, Number(result.percentage) || 0).toFixed(0)}% Score
              </div>
              <div className={`inline-block mt-2 px-4 py-2 rounded-full text-sm font-medium ${
                result.percentage >= 70 ? 'bg-green-100 text-green-800' : 'bg-yellow-100 text-yellow-800'
              }`}>
                {result.percentage >= 70 ? 'Passed!' : 'Keep practicing!'}
              </div>
            </div>

            {/* Mastery Update */}
            {mastery && (
              <div className={`rounded-lg p-4 mb-6 ${
                mastery.mastered ? 'bg-green-50 border border-green-200' : 'bg-yellow-50 border border-yellow-200'
              }`}>
                <h3 className="font-semibold mb-2">Topic Mastery: {mastery.topic_name}</h3>
                <div className="flex items-center gap-3">
                  <div className="flex-1">
                    <div className="flex justify-between text-sm mb-1">
                      <span>Average Score</span>
                      <span>{mastery.avg_score !== null ? `${mastery.avg_score}%` : 'N/A'}</span>
                    </div>
                    <div className="w-full bg-gray-200 rounded-full h-3">
                      <div
                        className={`h-3 rounded-full transition-all ${
                          mastery.mastered ? 'bg-green-500' : 'bg-yellow-500'
                        }`}
                        style={{ width: `${Math.min(mastery.avg_score || 0, 100)}%` }}
                      ></div>
                    </div>
                  </div>
                  <div className={`px-3 py-1 rounded-full text-sm font-medium ${
                    mastery.mastered ? 'bg-green-100 text-green-800' : 'bg-yellow-100 text-yellow-800'
                  }`}>
                    {mastery.mastered ? 'Mastered!' : `${mastery.threshold}% to master`}
                  </div>
                </div>
                {mastery.mastered && (
                  <p className="text-sm text-green-700 mt-2">
                    You have mastered this topic! New topics may now be available.
                  </p>
                )}
              </div>
            )}

            {/* Actions */}
            <div className="flex gap-3">
              <button
                onClick={() => navigate('/student/dashboard')}
                className="flex-1 bg-blue-600 text-white py-3 rounded-lg hover:bg-blue-700 font-medium"
              >
                Back to Dashboard
              </button>
            </div>
          </div>
        </div>
      </div>
    );
  }

  const currentQ = quiz.questions[currentQuestion];
  const isLastQuestion = currentQuestion === quiz.questions.length - 1;

  return (
    <div className="min-h-screen bg-gray-100 py-8">
      <div className="container mx-auto max-w-2xl">
        <div className="bg-white rounded-lg shadow-md p-6">
          <h1 className="text-2xl font-bold text-blue-600 mb-2">{quiz.title}</h1>
          <p className="text-gray-600 mb-4">Topic: {quiz.topic}</p>
          {error && (
            <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg mb-4 text-sm">
              {error}
            </div>
          )}
          <div className="mb-4 text-sm text-gray-500">Question {currentQuestion + 1} of {quiz.questions.length}</div>
          <div className="mb-6">
            <h3 className="text-lg font-semibold mb-4">{currentQ.question_text}</h3>
            {currentQ.question_image && (
              <div className="mb-4 flex justify-center bg-gray-50 rounded-lg p-3 border border-gray-200">
                <img
                  src={resolveUploadUrl(currentQ.question_image)}
                  alt="Question diagram"
                  className="max-w-full max-h-96 w-auto h-auto object-contain rounded-md"
                />
              </div>
            )}
            <div className="space-y-3">
              {currentQ.options.map((option, idx) => {
                const letter = String.fromCharCode(65 + idx);
                return (
                  <button key={idx} onClick={() => handleAnswer(letter)} className={`w-full text-left p-3 border rounded-lg ${answers[currentQuestion] === letter ? 'bg-blue-100 border-blue-500' : 'hover:bg-gray-50'}`}>
                    <span className="font-bold mr-2">{letter}.</span> {option}
                  </button>
                );
              })}
            </div>
          </div>
          <div className="flex justify-between">
            <button onClick={handlePrevious} disabled={currentQuestion === 0} className="px-4 py-2 bg-gray-300 rounded disabled:opacity-50">Previous</button>
            {!isLastQuestion ? (
              <button onClick={handleNext} className="px-4 py-2 bg-blue-600 text-white rounded">Next</button>
            ) : (
              <button onClick={handleSubmit} disabled={submitting} className="px-6 py-2 bg-green-600 text-white rounded font-medium disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2">
                {submitting && (
                  <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
                )}
                {submitting ? 'Submitting...' : 'Submit Quiz'}
              </button>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

export default QuizTaking;
