import { useState } from 'react'
import { Upload, X, Check, Sparkles } from 'lucide-react'
import { documentsApi, arabicApi } from '../lib/api'

interface PdfUploadProps {
  onTextExtracted: (text: string) => void
  disabled?: boolean
}

const SUPPORTED_EXTENSIONS = ['.pdf', '.epub', '.docx']

// Detect if text contains Arabic characters (more lenient for encoding issues)
const containsArabic = (text: string): boolean => {
  // Standard Arabic range
  const standardArabic = /[\u0600-\u06FF]/.test(text)
  if (standardArabic) return true

  // Arabic Presentation Forms (for encoded text)
  const presentationForms = /[\uFB50-\uFDFF\uFE70-\uFEFF]/.test(text)
  if (presentationForms) return true

  // Check for common Arabic patterns that might appear with encoding issues
  const arabicPatterns = /[\u0627-\u064a]/.test(text) // Basic letters
  return arabicPatterns
}

// Light cleanup for extracted text
const cleanupExtractedText = (text: string): string => {
  // Remove excessive whitespace
  return text.replace(/\n{4,}/g, '\n\n\n').trim()
}

export default function PdfUpload({ onTextExtracted, disabled }: PdfUploadProps) {
  const [isLoading, setIsLoading] = useState(false)
  const [uploadProgress, setUploadProgress] = useState(0)
  const [status, setStatus] = useState<'uploading' | 'extracting' | 'processing' | 'done' | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [result, setResult] = useState<{ chars: number; text: string; diacritized?: boolean; file_type?: string } | null>(null)
  const [isProcessingArabic, setIsProcessingArabic] = useState(false)

  const extractText = async (file: File) => {
    setIsLoading(true)
    setError(null)
    setUploadProgress(0)
    setStatus('uploading')
    setResult(null)

    try {
      const response = await documentsApi.extract(file, (progress) => {
        setUploadProgress(progress)
      })

      setStatus('extracting')
      setUploadProgress(0)

      // Simulate extraction progress
      const extractionInterval = setInterval(() => {
        setUploadProgress((prev) => {
          if (prev >= 90) {
            clearInterval(extractionInterval)
            return 90
          }
          return prev + Math.random() * 10
        })
      }, 200)

      if (!response.text.trim()) {
        clearInterval(extractionInterval)
        setError('No text found in document.')
        setStatus(null)
        return
      }

      clearInterval(extractionInterval)
      setUploadProgress(100)
      setStatus('done')
      
      // Light cleanup for extracted text
      const fixedText = cleanupExtractedText(response.text)
      
      // Debug Arabic detection
      const hasArabic = containsArabic(fixedText)
      console.log('Arabic detection:', hasArabic, 'Fixed text sample:', fixedText.substring(0, 100))
      
      setResult({ chars: response.total_chars, text: fixedText, file_type: response.file_type })
      onTextExtracted(fixedText)
    } catch (err) {
      setError('Failed to extract text from document')
      setStatus(null)
      console.error(err)
    } finally {
      setIsLoading(false)
    }
  }

  const handleFileSelect = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (!file) return

    // Check file extension
    const extension = file.name.toLowerCase().substring(file.name.lastIndexOf('.'))
    if (!SUPPORTED_EXTENSIONS.includes(extension)) {
      setError(`Unsupported file type: ${extension}. Please select PDF, EPUB, or DOCX.`)
      return
    }

    await extractText(file)
  }

  const handleDiacritize = async () => {
    if (!result) return

    setIsProcessingArabic(true)
    setStatus('processing')
    setError(null)

    try {
      const response = await arabicApi.diacritize(result.text)
      setResult({
        chars: response.processed_text.length,
        text: response.processed_text,
        diacritized: true
      })
      onTextExtracted(response.processed_text)
      setStatus('done')
    } catch (err) {
      setError('Failed to add diacritics')
      setStatus('done')
      console.error(err)
    } finally {
      setIsProcessingArabic(false)
    }
  }

  const handleClear = () => {
    setResult(null)
    setStatus(null)
    setError(null)
    setUploadProgress(0)
  }

  return (
    <div className="space-y-3">
      {!result && (
        <>
          <input
            type="file"
            accept=".pdf"
            onChange={handleFileSelect}
            disabled={disabled || isLoading}
            className="hidden"
            id="pdf-upload"
          />
          <label
            htmlFor="pdf-upload"
            className={`inline-flex items-center gap-2 px-4 py-2 border-2 border-dashed border-gray-300 dark:border-gray-600 rounded-lg cursor-pointer hover:border-indigo-500 dark:hover:border-indigo-400 transition-colors ${
              disabled || isLoading ? 'opacity-50 cursor-not-allowed' : ''
            }`}
          >
            <Upload className="w-5 h-5 text-gray-600 dark:text-gray-400" />
            <span className="text-sm font-medium text-gray-700 dark:text-gray-300">
              {status === 'uploading' ? 'Uploading...' : status === 'extracting' ? 'Extracting...' : 'Upload PDF'}
            </span>
          </label>
        </>
      )}

      {isLoading && (
        <div className="space-y-2">
          <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2.5 overflow-hidden">
            <div
              className="bg-indigo-600 h-2.5 rounded-full transition-all duration-300 ease-out"
              style={{ width: `${uploadProgress}%` }}
            />
          </div>
          <div className="flex justify-between text-xs text-gray-600 dark:text-gray-400">
            <span>
              {status === 'uploading' ? 'Uploading PDF...' : 'Extracting text...'}
            </span>
            <span>{Math.round(uploadProgress)}%</span>
          </div>
        </div>
      )}

      {result && status === 'done' && (
        <div className="space-y-2">
          <div className={`flex items-center justify-between p-3 border rounded-lg ${
            containsArabic(result.text)
              ? 'bg-green-50 dark:bg-green-900/20 border-green-200 dark:border-green-800'
              : 'bg-blue-50 dark:bg-blue-900/20 border-blue-200 dark:border-blue-800'
          }`}>
            <div className="flex flex-col gap-1">
              <div className="flex items-center gap-2">
                <Check className="w-5 h-5 text-green-600 dark:text-green-400" />
                <span className="text-sm text-green-700 dark:text-green-300">
                  Extracted {result.chars.toLocaleString()} characters
                  {result.diacritized && ' (with diacritics)'}
                </span>
              </div>
              {result?.file_type && (
                <span className="text-xs text-blue-700 dark:text-blue-300">
                  {result.file_type.toUpperCase()} file processed successfully
                </span>
              )}
            </div>
            <button
              onClick={handleClear}
              className="p-1 hover:bg-green-100 dark:hover:bg-green-900/30 rounded transition-colors"
            >
              <X className="w-4 h-4 text-green-600 dark:text-green-400" />
            </button>
          </div>
          {containsArabic(result.text) && !result.diacritized && (
            <button
              onClick={handleDiacritize}
              disabled={isProcessingArabic}
              className="inline-flex items-center gap-2 px-3 py-2 text-sm font-medium text-purple-700 dark:text-purple-300 bg-purple-50 dark:bg-purple-900/20 border border-purple-200 dark:border-purple-800 rounded-lg hover:bg-purple-100 dark:hover:bg-purple-900/30 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <Sparkles className="w-4 h-4" />
              {isProcessingArabic ? 'Adding diacritics...' : 'Add Diacritics (Tachkil)'}
            </button>
          )}
          {containsArabic(result.text) && (
            <span className="text-xs text-green-600 dark:text-green-400">
              ✓ Arabic text detected
            </span>
          )}
        </div>
      )}

      {error && (
        <div className="flex items-center justify-between p-3 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg">
          <div className="flex items-center gap-2">
            <X className="w-5 h-5 text-red-600 dark:text-red-400" />
            <span className="text-sm text-red-700 dark:text-red-300">{error}</span>
          </div>
          <button
            onClick={() => setError(null)}
            className="p-1 hover:bg-red-100 dark:hover:bg-red-900/30 rounded transition-colors"
          >
            <X className="w-4 h-4 text-red-600 dark:text-red-400" />
          </button>
        </div>
      )}
    </div>
  )
}
