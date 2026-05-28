import { useCallback, useEffect, useState } from 'react'
import { fetchInsightAnalytics, setUnauthorizedHandler } from './api'
import { clearAuthSession, getAuthUser, getToken } from './authStorage'
import AuthPage from './components/AuthPage'
import Dashboard from './components/Dashboard'
import DocumentUpload from './components/DocumentUpload'
import QuizInterface from './components/QuizInterface'

const SAMPLE_TEXT = `Photosynthesis is the process by which green plants and some other organisms use sunlight to synthesize foods from carbon dioxide and water. It occurs mainly in chloroplasts and produces oxygen as a byproduct. The light-dependent reactions take place in the thylakoid membranes, while the Calvin cycle occurs in the stroma. Chlorophyll absorbs light energy, which drives the conversion of ADP and NADP+ into ATP and NADPH. These molecules then fuel the fixation of carbon dioxide into glucose. Factors such as light intensity, carbon dioxide concentration, and temperature affect the rate of photosynthesis.`

export default function App() {
  const [authUser, setAuthUser] = useState(() => (getToken() ? getAuthUser() : null))
  const [educationalText, setEducationalText] = useState(SAMPLE_TEXT)
  const [activeText, setActiveText] = useState('')
  const [quizKey, setQuizKey] = useState(0)
  const [uploadQuizData, setUploadQuizData] = useState(null)
  const [score, setScore] = useState({ correct: 0, total: 0 })
  const [difficulty, setDifficulty] = useState(null)
  const [progress, setProgress] = useState({ currentIndex: 0, total: 0 })
  const [analytics, setAnalytics] = useState(null)
  const [analyticsLoading, setAnalyticsLoading] = useState(false)

  const handleLogout = useCallback(() => {
    clearAuthSession()
    setAuthUser(null)
    setActiveText('')
    setAnalytics(null)
  }, [])

  useEffect(() => {
    setUnauthorizedHandler(() => {
      setAuthUser(null)
    })
    return () => setUnauthorizedHandler(null)
  }, [])

  const loadAnalytics = useCallback(async () => {
    if (!authUser) return
    setAnalyticsLoading(true)
    try {
      const data = await fetchInsightAnalytics()
      setAnalytics(data)
    } catch {
      /* keep previous analytics on transient errors */
    } finally {
      setAnalyticsLoading(false)
    }
  }, [authUser])

  useEffect(() => {
    loadAnalytics()
  }, [loadAnalytics])

  const handleAnswerSubmitted = useCallback(() => {
    loadAnalytics()
    const pollDelays = [2000, 4000, 6000]
    pollDelays.forEach((delay) => {
      setTimeout(() => loadAnalytics(), delay)
    })
  }, [loadAnalytics])

  function startQuiz() {
    setUploadQuizData(null)
    setActiveText(educationalText.trim())
    setScore({ correct: 0, total: 0 })
    setDifficulty(null)
    setProgress({ currentIndex: 0, total: 0 })
    setQuizKey((k) => k + 1)
  }

  function handlePdfQuizReady(data) {
    setUploadQuizData(data)
    setActiveText(data.extracted_text_preview || '')
    setScore({ correct: 0, total: 0 })
    setDifficulty(data.difficulty)
    setProgress({ currentIndex: 0, total: data.questions.length })
    setQuizKey((k) => k + 1)
  }

  if (!authUser) {
    return (
      <AuthPage
        onAuthenticated={(data) =>
          setAuthUser({ user_id: data.user_id, username: data.username })
        }
      />
    )
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-white to-indigo-50/40">
      <header className="border-b border-slate-200/80 bg-white/80 backdrop-blur">
        <div className="mx-auto flex max-w-6xl flex-wrap items-center justify-between gap-4 px-4 py-5 sm:px-6">
          <div>
            <p className="text-xs font-semibold uppercase tracking-widest text-indigo-600">
              Adaptive learning
            </p>
            <h1 className="text-2xl font-bold text-slate-900">MCQ Diagnostic Quiz</h1>
          </div>
          <div className="flex items-center gap-3">
            <p className="rounded-lg bg-slate-100 px-3 py-1.5 text-sm text-slate-700">
              <span className="font-medium">{authUser.username}</span>
            </p>
            <button
              type="button"
              onClick={handleLogout}
              className="rounded-lg border border-slate-200 px-3 py-1.5 text-sm font-medium text-slate-600 hover:bg-slate-50"
            >
              Log out
            </button>
          </div>
        </div>
      </header>

      <main className="mx-auto grid max-w-6xl gap-6 px-4 py-8 lg:grid-cols-[1fr_300px] sm:px-6">
        <div className="space-y-6">
          <section className="rounded-2xl border border-slate-200/80 bg-white p-5 shadow-sm sm:p-6">
            <label htmlFor="educational-text" className="block text-sm font-semibold text-slate-900">
              Educational content
            </label>
            <p className="mt-1 text-xs text-slate-500">
              Upload a PDF or paste study material — questions are generated from that content only.
            </p>

            <div className="mt-4">
              <DocumentUpload
                onQuizReady={handlePdfQuizReady}
                onTextExtracted={(preview) => {
                  if (preview) setEducationalText(preview)
                }}
              />
            </div>

            <p className="mt-5 text-xs font-medium uppercase tracking-wide text-slate-400">
              Or paste text manually
            </p>
            <textarea
              id="educational-text"
              rows={5}
              value={educationalText}
              onChange={(e) => setEducationalText(e.target.value)}
              className="mt-3 w-full resize-y rounded-xl border border-slate-200 px-4 py-3 text-sm text-slate-800 outline-none ring-indigo-500 focus:ring-2"
            />
            <button
              type="button"
              onClick={startQuiz}
              disabled={!educationalText.trim()}
              className="mt-4 rounded-lg bg-indigo-600 px-5 py-2.5 text-sm font-semibold text-white shadow-sm hover:bg-indigo-700 disabled:cursor-not-allowed disabled:opacity-50"
            >
              {quizKey === 0 ? 'Start quiz' : 'Generate new quiz'}
            </button>
          </section>

          {activeText && (
            <QuizInterface
              key={quizKey}
              educationalText={activeText}
              quizKey={quizKey}
              initialQuizData={uploadQuizData}
              onScoreChange={setScore}
              onDifficultyChange={setDifficulty}
              onProgressChange={setProgress}
              onAnswerSubmitted={handleAnswerSubmitted}
            />
          )}
        </div>

        <Dashboard
          score={score}
          difficulty={difficulty}
          totalQuestions={progress.total}
          currentIndex={progress.currentIndex}
          analytics={analytics}
          analyticsLoading={analyticsLoading}
        />
      </main>
    </div>
  )
}
