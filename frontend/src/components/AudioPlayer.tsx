import { useState } from 'react'
import { Play, Pause } from 'lucide-react'

interface AudioPlayerProps {
  audioUrl: string
  duration?: number | null
}

export default function AudioPlayer({ audioUrl, duration }: AudioPlayerProps) {
  const [isPlaying, setIsPlaying] = useState(false)

  const togglePlay = () => {
    const audio = document.getElementById(`audio-${audioUrl}`) as HTMLAudioElement
    if (audio) {
      if (isPlaying) {
        audio.pause()
      } else {
        audio.play()
      }
      setIsPlaying(!isPlaying)
    }
  }

  return (
    <div className="flex items-center gap-4">
      <button
        onClick={togglePlay}
        className="p-2 bg-indigo-600 text-white rounded-full hover:bg-indigo-700 transition-colors"
      >
        {isPlaying ? <Pause className="w-5 h-5" /> : <Play className="w-5 h-5 ml-0.5" />}
      </button>
      {duration && <span className="text-sm text-gray-600 dark:text-gray-400">{Math.floor(duration / 60)}:{(duration % 60).toFixed(0).padStart(2, '0')}</span>}
      <audio
        id={`audio-${audioUrl}`}
        src={audioUrl}
        onEnded={() => setIsPlaying(false)}
        className="hidden"
      />
    </div>
  )
}
