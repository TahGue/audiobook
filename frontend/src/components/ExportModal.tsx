import { useState } from 'react'
import { X, Download, FileAudio } from 'lucide-react'
import { save } from '@tauri-apps/plugin-dialog'

interface ExportModalProps {
  isOpen: boolean
  onClose: () => void
  onExport: (format: 'mp3' | 'wav' | 'flac', quality: '128k' | '192k' | '320k') => void
  isExporting: boolean
}

export default function ExportModal({ isOpen, onClose, onExport, isExporting }: ExportModalProps) {
  const [format, setFormat] = useState<'mp3' | 'wav' | 'flac'>('mp3')
  const [quality, setQuality] = useState<'128k' | '192k' | '320k'>('192k')

  if (!isOpen) return null

  const handleExport = () => {
    onExport(format, quality)
  }

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white dark:bg-gray-800 rounded-xl p-6 shadow-xl max-w-md w-full mx-4">
        <div className="flex items-center justify-between mb-6">
          <h2 className="text-xl font-semibold text-gray-900 dark:text-white flex items-center gap-2">
            <FileAudio className="w-5 h-5 text-indigo-600" />
            Export Audiobook
          </h2>
          <button
            onClick={onClose}
            className="p-2 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg transition-colors"
          >
            <X className="w-5 h-5 text-gray-600 dark:text-gray-400" />
          </button>
        </div>

        <div className="space-y-6">
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              Audio Format
            </label>
            <div className="grid grid-cols-3 gap-3">
              {(['mp3', 'wav', 'flac'] as const).map((f) => (
                <button
                  key={f}
                  onClick={() => setFormat(f)}
                  className={`px-4 py-3 rounded-lg border-2 transition-colors ${
                    format === f
                      ? 'border-indigo-600 bg-indigo-50 dark:bg-indigo-900/20 text-indigo-700 dark:text-indigo-300'
                      : 'border-gray-300 dark:border-gray-600 hover:border-gray-400 dark:hover:border-gray-500'
                  }`}
                >
                  <div className="text-center">
                    <div className="font-semibold uppercase">{f}</div>
                    <div className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                      {f === 'mp3' ? 'Compressed' : f === 'wav' ? 'Lossless' : 'High Quality'}
                    </div>
                  </div>
                </button>
              ))}
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              Quality (MP3 only)
            </label>
            <select
              value={quality}
              onChange={(e) => setQuality(e.target.value as '128k' | '192k' | '320k')}
              disabled={format !== 'mp3'}
              className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white disabled:opacity-50"
            >
              <option value="128k">128 kbps (Smaller files)</option>
              <option value="192k">192 kbps (Balanced)</option>
              <option value="320k">320 kbps (Best quality)</option>
            </select>
          </div>

          <div className="flex gap-3">
            <button
              onClick={onClose}
              disabled={isExporting}
              className="flex-1 px-4 py-2 border border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors disabled:opacity-50"
            >
              Cancel
            </button>
            <button
              onClick={handleExport}
              disabled={isExporting}
              className="flex-1 flex items-center justify-center gap-2 px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 transition-colors disabled:opacity-50"
            >
              {isExporting ? (
                <>
                  <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
                  Exporting...
                </>
              ) : (
                <>
                  <Download className="w-4 h-4" />
                  Export
                </>
              )}
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}
