function ScoreBar({ label, value, max = 5, colorClass }) {
  const percent = max > 0 ? (value / max) * 100 : 0
  return (
    <div>
      <div className="flex items-center justify-between text-xs">
        <span className="font-medium text-slate-600">{label}</span>
        <span className="font-semibold text-slate-900">
          {value.toFixed(1)} / {max}
        </span>
      </div>
      <div className="mt-1.5 h-2 overflow-hidden rounded-full bg-slate-100">
        <div
          className={`h-full rounded-full transition-all duration-500 ${colorClass}`}
          style={{ width: `${percent}%` }}
        />
      </div>
    </div>
  )
}

export default function Dashboard({
  score,
  difficulty,
  totalQuestions,
  currentIndex,
  analytics,
  analyticsLoading,
}) {
  const answered = score.total
  const accuracy = answered > 0 ? Math.round((score.correct / answered) * 100) : 0
  const difficultyPercent = difficulty != null ? (difficulty / 10) * 100 : 0

  const hasAnalytics = analytics && analytics.total_evaluations > 0

  return (
    <aside className="space-y-5">
      <div className="rounded-2xl border border-slate-200/80 bg-white p-6 shadow-sm">
        <h2 className="text-lg font-semibold text-slate-900">Your progress</h2>
        <p className="mt-1 text-sm text-slate-500">Live stats for this session</p>

        <div className="mt-6 space-y-5">
          <div className="rounded-xl bg-slate-50 p-4">
            <p className="text-xs font-medium uppercase tracking-wide text-slate-500">
              Score
            </p>
            <p className="mt-1 text-3xl font-bold text-slate-900">
              {score.correct}
              <span className="text-lg font-medium text-slate-400"> / {answered}</span>
            </p>
            <p className="mt-1 text-sm text-slate-600">{accuracy}% accuracy</p>
          </div>

          <div className="rounded-xl bg-indigo-50 p-4">
            <p className="text-xs font-medium uppercase tracking-wide text-indigo-600">
              Adaptive difficulty level
            </p>
            <p className="mt-1 text-3xl font-bold text-indigo-900">
              {difficulty ?? '—'}
              <span className="text-lg font-medium text-indigo-400"> / 10</span>
            </p>
            <div className="mt-3 h-2 overflow-hidden rounded-full bg-indigo-100">
              <div
                className="h-full rounded-full bg-indigo-500 transition-all duration-500"
                style={{ width: `${difficultyPercent}%` }}
              />
            </div>
            <p className="mt-2 text-xs text-indigo-700/80">
              Adjusts as you answer questions correctly or incorrectly.
            </p>
          </div>

          {totalQuestions > 0 && (
            <div className="rounded-xl border border-dashed border-slate-200 p-4">
              <p className="text-xs font-medium uppercase tracking-wide text-slate-500">
                Quiz progress
              </p>
              <p className="mt-1 text-sm text-slate-700">
                Question {Math.min(currentIndex + 1, totalQuestions)} of {totalQuestions}
              </p>
            </div>
          )}
        </div>
      </div>

      <div className="rounded-2xl border border-violet-200/80 bg-gradient-to-br from-violet-50 to-white p-6 shadow-sm">
        <h2 className="text-lg font-semibold text-slate-900">Insight analytics</h2>
        <p className="mt-1 text-sm text-slate-500">
          LLM quality scores for generated questions
        </p>

        {analyticsLoading && !hasAnalytics && (
          <p className="mt-6 text-sm text-slate-500">Evaluating question quality…</p>
        )}

        {!analyticsLoading && !hasAnalytics && (
          <p className="mt-6 text-sm text-slate-500">
            Answer a question to trigger background quality evaluation.
          </p>
        )}

        {hasAnalytics && (
          <div className="mt-6 space-y-5">
            <div className="grid grid-cols-2 gap-3">
              <div className="rounded-xl bg-white/80 p-3 ring-1 ring-violet-100">
                <p className="text-[10px] font-semibold uppercase tracking-wide text-violet-600">
                  Evaluations
                </p>
                <p className="mt-1 text-2xl font-bold text-slate-900">
                  {analytics.total_evaluations}
                </p>
              </div>
              <div className="rounded-xl bg-white/80 p-3 ring-1 ring-violet-100">
                <p className="text-[10px] font-semibold uppercase tracking-wide text-violet-600">
                  Overall avg
                </p>
                <p className="mt-1 text-2xl font-bold text-slate-900">
                  {analytics.avg_overall}
                  <span className="text-sm font-medium text-slate-400"> / 5</span>
                </p>
              </div>
            </div>

            <ScoreBar
              label="Relevance"
              value={analytics.avg_relevance}
              colorClass="bg-violet-500"
            />
            <ScoreBar
              label="Clarity"
              value={analytics.avg_clarity}
              colorClass="bg-fuchsia-500"
            />

            {analytics.recent_evaluations?.length > 0 && (
              <div>
                <p className="text-xs font-medium uppercase tracking-wide text-slate-500">
                  Recent evaluations
                </p>
                <ul className="mt-2 space-y-2">
                  {analytics.recent_evaluations.map((item) => (
                    <li
                      key={item.question_id}
                      className="rounded-lg bg-white/90 px-3 py-2 text-xs ring-1 ring-slate-100"
                    >
                      <p className="line-clamp-2 text-slate-700">{item.question_preview}</p>
                      <p className="mt-1 text-slate-500">
                        Relevance {item.relevance}/5 · Clarity {item.clarity}/5 ·{' '}
                        {item.user_was_correct ? 'Correct' : 'Incorrect'}
                      </p>
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        )}

        {analyticsLoading && hasAnalytics && (
          <p className="mt-4 text-xs text-violet-600">Refreshing metrics…</p>
        )}
      </div>
    </aside>
  )
}
