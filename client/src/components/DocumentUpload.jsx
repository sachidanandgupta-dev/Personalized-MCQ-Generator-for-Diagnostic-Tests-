import { useCallback, useRef, useState } from 'react'
import { uploadDocument } from '../api'

export default function DocumentUpload({ onQuizReady, onTextExtracted }) {
  const inputRef = useRef(null)
  const [dragging, setDragging] = useState(false)
  const [uploading, setUploading] = useState(false)
  const [error, setError] = useState(null)
  const [lastMeta, setLastMeta] = useState(null)

  const handleFile = useCallback(
    async (file) => {
      if (!file) return
      if (file.type !== 'application/pdf' && !file.name.toLowerCase().endsWith('.pdf')) {
        setError('Please upload a PDF file.')
        return
      }

      setError(null)
      setUploading(true)
      setLastMeta(null)

      try {
        const data = await uploadDocument(file)
        setLastMeta({
          filename: data.source_filename,
          totalChunks: data.total_chunks,
          extractedChars: data.extracted_char_count,
        })
        onTextExtracted?.(data.extracted_text_preview)
        onQuizReady?.(data)
      } catch (err) {
        setError(err.message ?? 'Failed to process PDF.')
      } finally {
        setUploading(false)
      }
    },
    [onQuizReady, onTextExtracted],
  )

  function onDrop(event) {
    event.preventDefault()
    setDragging(false)
    const file = event.dataTransfer.files?.[0]
    handleFile(file)
  }

  function onDragOver(event) {
    event.preventDefault()
    setDragging(true)
  }

  function onDragLeave() {
    setDragging(false)
  }

  function onFileChange(event) {
    handleFile(event.target.files?.[0])
    event.target.value = ''
  }

  return (
    <div className="space-y-3">
      <div
        role="button"
        tabIndex={0}
        onKeyDown={(e) => e.key === 'Enter' && inputRef.current?.click()}
        onDrop={onDrop}
        onDragOver={onDragOver}
        onDragLeave={onDragLeave}
        onClick={() => !uploading && inputRef.current?.click()}
        className={`relative cursor-pointer rounded-xl border-2 border-dashed px-6 py-10 text-center transition ${
          dragging
            ? 'border-indigo-500 bg-indigo-50'
            : 'border-slate-300 bg-slate-50/50 hover:border-indigo-400 hover:bg-indigo-50/30'
        } ${uploading ? 'pointer-events-none opacity-70' : ''}`}
      >
        <input
          ref={inputRef}
          type="file"
          accept="application/pdf,.pdf"
          className="hidden"
          onChange={onFileChange}
        />

        <div className="mx-auto flex h-12 w-12 items-center justify-center rounded-full bg-indigo-100 text-indigo-600">
          <svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12"
            />
          </svg>
        </div>

        <p className="mt-3 text-sm font-semibold text-slate-800">
          {uploading ? 'Extracting text & generating questions…' : 'Drag & drop a PDF here'}
        </p>
        <p className="mt-1 text-xs text-slate-500">or click to browse · max 10 MB</p>

        {uploading && (
          <div className="absolute inset-0 flex items-center justify-center rounded-xl bg-white/60">
            <div className="h-8 w-8 animate-spin rounded-full border-2 border-indigo-600 border-t-transparent" />
          </div>
        )}
      </div>

      {error && (
        <p className="rounded-lg bg-red-50 px-3 py-2 text-sm text-red-700">{error}</p>
      )}

      {lastMeta && !uploading && (
        <p className="text-xs text-slate-600">
          Processed <span className="font-medium">{lastMeta.filename}</span> (
          {lastMeta.extractedChars.toLocaleString()} characters
          {lastMeta.totalChunks > 1
            ? ` · used chunk 1 of ${lastMeta.totalChunks} for this quiz`
            : ''}
          )
        </p>
      )}
    </div>
  )
}
