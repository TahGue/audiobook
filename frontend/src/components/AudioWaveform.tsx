import { useEffect, useRef, useState, useCallback } from 'react'
import WaveSurfer from 'wavesurfer.js'
import { Play, Pause, SkipBack, SkipForward, ZoomIn, ZoomOut, Scissors } from 'lucide-react'

interface AudioWaveformProps {
  audioUrl: string
  onTrim?: (start: number, end: number) => void
  onRegionChange?: (start: number, end: number) => void
}

export default function AudioWaveform({ audioUrl, onTrim, onRegionChange }: AudioWaveformProps) {
  const waveformRef = useRef<HTMLDivElement>(null)
  const wavesurfer = useRef<WaveSurfer | null>(null)
  const [isPlaying, setIsPlaying] = useState(false)
  const [currentTime, setCurrentTime] = useState(0)
  const [duration, setDuration] = useState(0)
  const [zoom, setZoom] = useState(50)
  const [region, setRegion] = useState<{ start: number; end: number } | null>(null)
  const [isLoading, setIsLoading] = useState(true)

  useEffect(() => {
    if (!waveformRef.current) return

    // Initialize WaveSurfer
    const ws = WaveSurfer.create({
      container: waveformRef.current,
      waveColor: '#4f46e5',
      progressColor: '#4338ca',
      cursorColor: '#dc2626',
      cursorWidth: 2,
      barWidth: 2,
      barGap: 1,
      barRadius: 2,
      height: 120,
      normalize: true,
      interact: true,
      dragToSeek: true,
      minPxPerSec: zoom,
    })

    wavesurfer.current = ws

    // Load audio
    ws.load(audioUrl)

    // Event listeners
    ws.on('ready', () => {
      setDuration(ws.getDuration())
      setIsLoading(false)
    })

    ws.on('play', () => setIsPlaying(true))
    ws.on('pause', () => setIsPlaying(false))
    ws.on('timeupdate', (time: number) => setCurrentTime(time))
    ws.on('finish', () => setIsPlaying(false))

    // Double-click to create region
    ws.on('dblclick', () => {
      const current = ws.getCurrentTime()
      const end = Math.min(current + 10, duration)
      setRegion({ start: current, end })
      if (onRegionChange) onRegionChange(current, end)
    })

    return () => {
      ws.destroy()
    }
  }, [audioUrl, zoom, duration, onRegionChange])

  const togglePlay = useCallback(() => {
    wavesurfer.current?.playPause()
  }, [])

  const skipBackward = useCallback(() => {
    const newTime = Math.max(0, currentTime - 5)
    wavesurfer.current?.setTime(newTime)
    setCurrentTime(newTime)
  }, [currentTime])

  const skipForward = useCallback(() => {
    const newTime = Math.min(duration, currentTime + 5)
    wavesurfer.current?.setTime(newTime)
    setCurrentTime(newTime)
  }, [duration, currentTime])

  const handleZoomIn = useCallback(() => {
    setZoom(prev => Math.min(prev + 20, 200))
  }, [])

  const handleZoomOut = useCallback(() => {
    setZoom(prev => Math.max(prev - 20, 10))
  }, [])

  const handleTrim = useCallback(() => {
    if (region && onTrim) {
      onTrim(region.start, region.end)
    }
  }, [region, onTrim])

  const formatTime = (seconds: number) => {
    const mins = Math.floor(seconds / 60)
    const secs = Math.floor(seconds % 60)
    const ms = Math.floor((seconds % 1) * 100)
    return `${mins}:${secs.toString().padStart(2, '0')}.${ms.toString().padStart(2, '0')}`
  }

  return (
    <div className="space-y-4">
      {/* Waveform */}
      <div className="relative">
        {isLoading && (
          <div className="absolute inset-0 flex items-center justify-center bg-gray-50 dark:bg-gray-900 rounded-lg">
            <div className="animate-spin h-8 w-8 border-4 border-indigo-500 border-t-transparent rounded-full" />
          </div>
        )}
        
        <div
          ref={waveformRef}
          className="w-full h-[120px] bg-gray-50 dark:bg-gray-900 rounded-lg overflow-hidden"
        />
        
        {/* Region overlay */}
        {region && (
          <div
            className="absolute top-0 h-full bg-indigo-500/20 border-x-2 border-indigo-500 pointer-events-none"
            style={{
              left: `${(region.start / duration) * 100}%`,
              width: `${((region.end - region.start) / duration) * 100}%`,
            }}
          />
        )}
      </div>

      {/* Time display */}
      <div className="flex justify-between text-sm text-gray-600 dark:text-gray-400">
        <span>{formatTime(currentTime)}</span>
        <span>{formatTime(duration)}</span>
      </div>

      {/* Controls */}
      <div className="flex items-center justify-between">
        {/* Playback controls */}
        <div className="flex items-center gap-2">
          <button
            onClick={skipBackward}
            className="p-2 hover:bg-gray-100 dark:hover:bg-gray-800 rounded-full transition-colors"
            title="Skip back 5s"
          >
            <SkipBack className="w-5 h-5" />
          </button>
          
          <button
            onClick={togglePlay}
            className="p-3 bg-indigo-600 hover:bg-indigo-700 text-white rounded-full transition-colors"
          >
            {isPlaying ? (
              <Pause className="w-6 h-6" />
            ) : (
              <Play className="w-6 h-6 ml-0.5" />
            )}
          </button>
          
          <button
            onClick={skipForward}
            className="p-2 hover:bg-gray-100 dark:hover:bg-gray-800 rounded-full transition-colors"
            title="Skip forward 5s"
          >
            <SkipForward className="w-5 h-5" />
          </button>
        </div>

        {/* Zoom and edit controls */}
        <div className="flex items-center gap-2">
          <button
            onClick={handleZoomOut}
            className="p-2 hover:bg-gray-100 dark:hover:bg-gray-800 rounded-lg transition-colors"
            title="Zoom out"
          >
            <ZoomOut className="w-5 h-5" />
          </button>
          
          <span className="text-sm text-gray-500 w-16 text-center">
            {zoom}px/s
          </span>
          
          <button
            onClick={handleZoomIn}
            className="p-2 hover:bg-gray-100 dark:hover:bg-gray-800 rounded-lg transition-colors"
            title="Zoom in"
          >
            <ZoomIn className="w-5 h-5" />
          </button>
          
          {region && onTrim && (
            <button
              onClick={handleTrim}
              className="flex items-center gap-2 px-3 py-2 bg-green-600 hover:bg-green-700 text-white rounded-lg transition-colors"
              title="Trim to selection"
            >
              <Scissors className="w-4 h-4" />
              <span className="text-sm">Trim</span>
            </button>
          )}
        </div>
      </div>

      {/* Instructions */}
      <p className="text-xs text-gray-500 text-center">
        Double-click waveform to create selection region • Drag to seek
      </p>
    </div>
  )
}
