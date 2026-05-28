import { useCallback, useEffect, useState } from 'react'
import { generateMcqs, submitAnswer } from '../api'

export default function QuizInterface({
  educationalText,
  quizKey,
  initialQuizData = null,
  onScoreChange,
  onDifficultyChange,
  onProgressChange,
  onAnswerSubmitted,
}) {
  const [questions, setQuestions] = useState([])
  const [currentIndex, setCurrentIndex] = useState(0)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [selectedOption, setSelectedOption] = useState(null)
  const [revealed, setRevealed] = useState(false)
  const [submitting, setSubmitting] = useState(false)

  const applyQuizData = useCallback(
    (data) => {
      const withIds = data.questions.map((q) => ({
        ...q,
        id: q.question_id,
      }))
      setQuestions(withIds)
      onDifficultyChange?.(data.difficulty)
      onProgressChange?.({ currentIndex: 0, total: withIds.length })
    },
    [onDifficultyChange, onProgressChange],
  )

  const loadQuiz = useCallback(async () => {
    setLoading(true)
    setError(null)
    setQuestions([])
    setCurrentIndex(0)
    setSelectedOption(null)
    setRevealed(false)

    try {
      const data = await generateMcqs(educationalText)
      applyQuizData(data)
    } catch (err) {
      setError(err.message ?? 'Failed to load questions.')
    } finally {
      setLoading(false)
    }
  }, [educationalText, applyQuizData])

  useEffect(() => {
    setError(null)
    setQuestions([])
    setCurrentIndex(0)
    setSelectedOption(null)
    setRevealed(false)

    if (initialQuizData) {
      setLoading(false)
      applyQuizData(initialQuizData)
      return
    }

    if (educationalText?.trim()) {
      loadQuiz()
    }
  }, [educationalText, quizKey, initialQuizData, loadQuiz, applyQuizData])

  const current = questions[currentIndex]
  const isLast = currentIndex >= questions.length - 1

  async function handleSelect(option) {
    if (revealed || submitting || !current) return

    const isCorrect = option === current.correct_answer
    setSelectedOption(option)
    setRevealed(true)
    setSubmitting(true)

    onScoreChange?.((prev) => ({
      correct: prev.correct + (isCorrect ? 1 : 0),
      total: prev.total + 1,
    }))

    try {
      const result = await submitAnswer(current.id, isCorrect)
      onDifficultyChange?.(result.difficulty)
      onAnswerSubmitted?.()
    } catch (err) {
      setError(err.message ?? 'Failed to submit answer.')
    } finally {
      setSubmitting(false)
    }
  }

  function handleNext() {
    if (isLast) return
    setCurrentIndex((i) => i + 1)
    setSelectedOption(null)
    setRevealed(false)
    onProgressChange?.({ currentIndex: currentIndex + 1, total: questions.length })
  }

  if (loading) {
    return (
      <div className="flex min-h-[420px] items-center justify-center rounded-2xl border border-slate-200/80 bg-white p-10 shadow-sm">
        <div className="text-center">
          <div className="mx-auto h-10 w-10 animate-spin rounded-full border-2 border-indigo-600 border-t-transparent" />
          <p className="mt-4 text-sm font-medium text-slate-600">
            Generating personalized questions…
          </p>
          <p className="mt-1 text-xs text-slate-400">This may take a few seconds</p>
        </div>
      </div>
    )
  }

  if (error && questions.length === 0) {
    return (
      <div className="rounded-2xl border border-red-200 bg-red-50 p-8 text-center shadow-sm">
        <p className="font-medium text-red-800">Could not load quiz</p>
        <p className="mt-2 text-sm text-red-600">{error}</p>
        <button
          type="button"
          onClick={loadQuiz}
          className="mt-4 rounded-lg bg-red-600 px-4 py-2 text-sm font-medium text-white hover:bg-red-700"
        >
          Try again
        </button>
      </div>
    )
  }

  if (!current) {
    return (
      <div className="rounded-2xl border border-slate-200/80 bg-white p-10 text-center shadow-sm">
        <p className="text-slate-600">No questions available.</p>
      </div>
    )
  }

  return (
    <div className="rounded-2xl border border-slate-200/80 bg-white p-6 shadow-sm sm:p-8">
      <div className="mb-6 flex items-center justify-between gap-4">
        <span className="rounded-full bg-indigo-50 px-3 py-1 text-xs font-semibold text-indigo-700">
          Question {currentIndex + 1} of {questions.length}
        </span>
        {submitting && (
          <span className="text-xs text-slate-400">Saving result…</span>
        )}
      </div>

      <h2 className="text-xl font-semibold leading-snug text-slate-900 sm:text-2xl">
        {current.question}
      </h2>

      <ul className="mt-8 space-y-3">
        {current.options.map((option) => {
          const isSelected = selectedOption === option
          const isCorrectOption = option === current.correct_answer
          let style =
            'border-slate-200 bg-white text-slate-800 hover:border-indigo-300 hover:bg-indigo-50/50'

          if (revealed) {
            if (isCorrectOption) {
              style = 'border-emerald-500 bg-emerald-50 text-emerald-900'
            } else if (isSelected && !isCorrectOption) {
              style = 'border-red-400 bg-red-50 text-red-900'
            } else {
              style = 'border-slate-100 bg-slate-50 text-slate-500'
            }
          } else if (isSelected) {
            style = 'border-indigo-500 bg-indigo-50 text-indigo-900'
          }

          return (
            <li key={option}>
              <button
                type="button"
                disabled={revealed}
                onClick={() => handleSelect(option)}
                className={`w-full rounded-xl border-2 px-4 py-3 text-left text-sm font-medium transition ${style} disabled:cursor-default`}
              >
                {option}
              </button>
            </li>
          )
        })}
      </ul>

      {revealed && (
        <div
          className={`mt-6 rounded-xl border p-4 ${
            selectedOption === current.correct_answer
              ? 'border-emerald-200 bg-emerald-50'
              : 'border-amber-200 bg-amber-50'
          }`}
        >
          <p
            className={`text-sm font-semibold ${
              selectedOption === current.correct_answer
                ? 'text-emerald-800'
                : 'text-amber-800'
            }`}
          >
            {selectedOption === current.correct_answer ? 'Correct!' : 'Not quite'}
            {selectedOption !== current.correct_answer && (
              <span className="mt-1 block font-normal text-amber-700">
                Correct answer: {current.correct_answer}
              </span>
            )}
          </p>
          <p className="mt-2 text-sm leading-relaxed text-slate-700">
            {current.explanation}
          </p>
        </div>
      )}

      {error && questions.length > 0 && (
        <p className="mt-4 text-sm text-red-600">{error}</p>
      )}

      <div className="mt-8 flex justify-end">
        {isLast && revealed ? (
          <p className="text-sm font-medium text-slate-600">
            Quiz complete — start a new round from the sidebar.
          </p>
        ) : (
          <button
            type="button"
            onClick={handleNext}
            disabled={!revealed || isLast}
            className="rounded-lg bg-indigo-600 px-5 py-2.5 text-sm font-semibold text-white shadow-sm transition hover:bg-indigo-700 disabled:cursor-not-allowed disabled:opacity-40"
          >
            Next question
          </button>
        )}
      </div>
    </div>
  )
}
