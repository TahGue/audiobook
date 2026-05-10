import { useState, useEffect } from 'react'
import { Volume2 } from 'lucide-react'
import { ttsApi } from '../lib/api'
import { Chapter, Voice } from '../types/audiobook'

interface TTSControlsProps {
  chapter: Chapter
  onGenerated: () => void
}

export default function TTSControls({ chapter, onGenerated }: TTSControlsProps) {
  const [voices, setVoices] = useState<Voice[]>([])
  const [selectedVoice, setSelectedVoice] = useState('')
  const [isGenerating, setIsGenerating] = useState(false)

  useEffect(() => {
    loadVoices()
  }, [chapter.language])

  const loadVoices = async () => {
    try {
      const data = await ttsApi.getVoices(chapter.language)
      setVoices(data)
      if (data.length > 0 && !selectedVoice) {
        setSelectedVoice(data[0].id)
      }
    } catch (error) {
      console.error('Failed to load voices:', error)
    }
  }

  const handleGenerate = async () => {
    if (!selectedVoice) return

    setIsGenerating(true)
    try {
      await ttsApi.generate({
        chapter_id: chapter.id,
        voice_id: selectedVoice,
        language: chapter.language,
      })
      onGenerated()
    } catch (error) {
      console.error('Failed to generate TTS:', error)
    } finally {
      setIsGenerating(false)
    }
  }

  return (
    <div className="flex items-center gap-4">
      <select
        value={selectedVoice}
        onChange={(e) => setSelectedVoice(e.target.value)}
        disabled={isGenerating}
        className="px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg text-sm bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
      >
        {voices.map((voice) => (
          <option key={voice.id} value={voice.id}>
            {voice.name}
          </option>
        ))}
      </select>
      <button
        onClick={handleGenerate}
        disabled={isGenerating || !selectedVoice}
        className="flex items-center gap-2 px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
      >
        <Volume2 className="w-4 h-4" />
        {isGenerating ? 'Generating...' : 'Generate Audio'}
      </button>
    </div>
  )
}
