import { useState, useEffect } from 'react'
import { useParams, Link } from 'react-router-dom'
import { ArrowLeft, Plus, Trash2, GripVertical, Download, Scissors, Zap } from 'lucide-react'
import { projectsApi, chaptersApi, exportApi, ttsApi } from '../lib/api'
import { Project } from '../types/audiobook'
import PdfUpload from '../components/PdfUpload'
import TTSControls from '../components/TTSControls'
import AudioPlayer from '../components/AudioPlayer'
import ExportModal from '../components/ExportModal'
import { save } from '@tauri-apps/plugin-dialog'
import {
  DndContext,
  closestCenter,
  KeyboardSensor,
  PointerSensor,
  useSensor,
  useSensors,
  DragEndEvent,
} from '@dnd-kit/core'
import {
  arrayMove,
  SortableContext,
  sortableKeyboardCoordinates,
  useSortable,
  verticalListSortingStrategy,
} from '@dnd-kit/sortable'
import { CSS } from '@dnd-kit/utilities'

export default function ProjectDetail() {
  const { id } = useParams<{ id: string }>()
  const [project, setProject] = useState<Project | null>(null)
  const [loading, setLoading] = useState(true)
  const [showForm, setShowForm] = useState(false)
  const [title, setTitle] = useState('')
  const [content, setContent] = useState('')
  const [showExportModal, setShowExportModal] = useState(false)
  const [isExporting, setIsExporting] = useState(false)
  const [extractedText, setExtractedText] = useState('')
  const [showOneClickModal, setShowOneClickModal] = useState(false)
  const [isGenerating, setIsGenerating] = useState(false)
  const [generationProgress, setGenerationProgress] = useState(0)
  const [generationStatus, setGenerationStatus] = useState('')
  const [selectedVoice, setSelectedVoice] = useState('')
  const [voices, setVoices] = useState<any[]>([])

  const sensors = useSensors(
    useSensor(PointerSensor),
    useSensor(KeyboardSensor, {
      coordinateGetter: sortableKeyboardCoordinates,
    })
  )

  useEffect(() => {
    if (id) {
      loadProject()
      loadVoices()
    }
  }, [id])

  const loadVoices = async () => {
    if (!project) return
    try {
      const data = await ttsApi.getVoices(project.language)
      setVoices(data)
      if (data.length > 0) setSelectedVoice(data[0].id)
    } catch (error) {
      console.error('Failed to load voices:', error)
    }
  }

  const loadProject = async () => {
    if (!id) return
    try {
      const data = await projectsApi.get(id)
      setProject(data)
    } catch (error) {
      console.error('Failed to load project:', error)
    } finally {
      setLoading(false)
    }
  }

  const handleCreateChapter = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!id || !title.trim() || !content.trim()) return

    try {
      await chaptersApi.create({ title, content, project_id: id })
      setTitle('')
      setContent('')
      setShowForm(false)
      loadProject()
    } catch (error) {
      console.error('Failed to create chapter:', error)
    }
  }

  const handleDeleteChapter = async (chapterId: string) => {
    if (!confirm('Delete this chapter?')) return

    try {
      await chaptersApi.delete(chapterId)
      loadProject()
    } catch (error) {
      console.error('Failed to delete chapter:', error)
    }
  }

  const handleDragEnd = async (event: DragEndEvent) => {
    const { active, over } = event
    if (!over || !project || !project.chapters) return

    if (active.id !== over.id) {
      const oldIndex = project.chapters.findIndex((c) => c.id === active.id)
      const newIndex = project.chapters.findIndex((c) => c.id === over.id)
      
      const newChapters = arrayMove(project.chapters, oldIndex, newIndex)
      setProject({ ...project, chapters: newChapters })

      // Update order on backend
      try {
        await chaptersApi.reorder(active.id as string, newIndex)
      } catch (error) {
        console.error('Failed to reorder chapters:', error)
        loadProject() // Revert on error
      }
    }
  }

  const handleAutoSplit = async (text: string) => {
    if (!id) return
    try {
      const result = await chaptersApi.autoSplit({
        text,
        project_id: id,
        language: project?.language || 'en',
        target_length: 5000
      })
      // Add the split chapters
      for (const chapter of result.chapters) {
        await chaptersApi.create({
          title: chapter.title,
          content: chapter.content,
          project_id: id,
          language: project?.language || 'en'
        })
      }
      loadProject()
    } catch (error) {
      console.error('Failed to auto-split:', error)
    }
  }

  const handleOneClickGenerate = async () => {
    if (!id || !extractedText || !selectedVoice) return
    
    setIsGenerating(true)
    setGenerationProgress(0)
    setGenerationStatus('Starting...')
    
    try {
      await projectsApi.generateOneClickAudiobook(id, {
        document_path: 'temp.pdf', // Would be the actual uploaded file
        voice_id: selectedVoice,
        language: project?.language || 'en',
        format: 'mp3',
        quality: '192k',
        auto_split_chapters: true,
        target_chapter_length: 5000
      })
      
      // Poll for status
      const interval = setInterval(async () => {
        const status = await projectsApi.getOneClickStatus(id)
        setGenerationProgress(status.progress || 0)
        setGenerationStatus(status.current_step || '')
        
        if (status.status === 'completed') {
          clearInterval(interval)
          setIsGenerating(false)
          loadProject()
        } else if (status.status === 'failed') {
          clearInterval(interval)
          setIsGenerating(false)
          alert('Generation failed: ' + status.error)
        }
      }, 2000)
      
    } catch (error) {
      console.error('Failed to generate audiobook:', error)
      setIsGenerating(false)
      alert('Generation failed')
    }
  }

  const handleExport = async (format: 'mp3' | 'wav' | 'flac', quality: '128k' | '192k' | '320k') => {
    if (!id) return
    setIsExporting(true)
    try {
      // Try to use native save dialog in Tauri
      const filePath = await save({
        filters: [
          {
            name: 'Audio Files',
            extensions: [format]
          }
        ],
        defaultPath: `${project?.title || 'audiobook'}.${format}`
      })

      if (filePath) {
        await exportApi.exportProject(id, format, quality)
        setShowExportModal(false)
        alert(`Export complete! Saved to ${filePath}`)
      }
    } catch (err) {
      console.error('Failed to export:', err)
      // Fallback to regular export if Tauri dialog fails
      try {
        await exportApi.exportProject(id, format, quality)
        setShowExportModal(false)
        alert('Export complete!')
      } catch (fallbackErr) {
        console.error('Fallback export also failed:', fallbackErr)
        alert('Export failed. Please try again.')
      }
    } finally {
      setIsExporting(false)
    }
  }

  function SortableChapter({ chapter, projectId }: { chapter: any; projectId: string }) {
    const {
      attributes,
      listeners,
      setNodeRef,
      transform,
      transition,
      isDragging,
    } = useSortable({ id: chapter.id })

    const style = {
      transform: CSS.Transform.toString(transform),
      transition,
      opacity: isDragging ? 0.5 : 1,
    }

    return (
      <div ref={setNodeRef} style={style} className="bg-white dark:bg-gray-800 rounded-xl p-6 shadow-md">
        <div className="flex items-start justify-between mb-4">
          <div className="flex items-center gap-3 flex-1">
            <div {...attributes} {...listeners} className="cursor-grab active:cursor-grabbing">
              <GripVertical className="w-5 h-5 text-gray-400" />
            </div>
            <h3 className="text-xl font-semibold text-gray-900 dark:text-white">{chapter.title}</h3>
          </div>
          <div className="flex gap-2">
            <button onClick={() => handleDeleteChapter(chapter.id)} className="p-2 text-red-600 hover:bg-red-50 dark:hover:bg-red-900/20 rounded-lg transition-colors">
              <Trash2 className="w-5 h-5" />
            </button>
          </div>
        </div>
        <p 
          className="text-gray-700 dark:text-gray-300 mb-4 whitespace-pre-wrap text-right" 
          dir="auto"
          style={{ unicodeBidi: 'plaintext' }}
        >
          {chapter.content}
        </p>
        <div className="flex items-center justify-between pt-4 border-t border-gray-200 dark:border-gray-700">
          {chapter.audio_path && (
            <AudioPlayer audioUrl={`/audio/${projectId}/${chapter.id}.wav`} duration={chapter.duration_seconds} />
          )}
          <TTSControls chapter={chapter} onGenerated={loadProject} />
        </div>
      </div>
    )
  }

  if (loading) return <p className="text-center py-12">Loading...</p>
  if (!project) return <p className="text-center py-12 text-red-600">Project not found</p>

  return (
    <div className="max-w-4xl mx-auto p-6">
      <div className="flex items-center gap-4 mb-8">
        <Link to="/" className="p-2 hover:bg-gray-100 dark:hover:bg-gray-800 rounded-lg transition-colors">
          <ArrowLeft className="w-6 h-6 text-gray-600 dark:text-gray-400" />
        </Link>
        <h1 className="text-3xl font-bold text-gray-900 dark:text-white flex-1">{project.title}</h1>
        <div className="flex gap-2">
          {extractedText && (
            <button
              onClick={() => setShowOneClickModal(true)}
              disabled={isGenerating}
              className="flex items-center gap-2 px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition-colors disabled:opacity-50"
            >
              <Zap className="w-4 h-4" />
              {isGenerating ? 'Generating...' : 'One-Click Audiobook'}
            </button>
          )}
          <button
            onClick={() => setShowExportModal(true)}
            className="flex items-center gap-2 px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors"
          >
            <Download className="w-4 h-4" />
            Export
          </button>
        </div>
      </div>

      {showForm && (
        <form onSubmit={handleCreateChapter} className="bg-white dark:bg-gray-800 rounded-xl p-6 shadow-md mb-6">
          <div className="space-y-4">
            <input
              type="text"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              placeholder="Chapter title"
              className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
              autoFocus
            />
            <PdfUpload onTextExtracted={(text) => { setContent(text); setExtractedText(text); }} />
            <textarea
              value={content}
              onChange={(e) => setContent(e.target.value)}
              placeholder="Chapter content..."
              rows={8}
              dir="auto"
              className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white resize-y text-right"
              style={{ unicodeBidi: 'plaintext' }}
            />
            {extractedText && extractedText.length > 5000 && (
              <button
                type="button"
                onClick={() => handleAutoSplit(extractedText)}
                className="flex items-center gap-2 px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition-colors"
              >
                <Scissors className="w-4 h-4" />
                Auto-Split into Chapters
              </button>
            )}
            <div className="flex gap-2">
              <button type="submit" className="px-6 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors">
                Add Chapter
              </button>
              <button type="button" onClick={() => { setShowForm(false); setContent(''); setExtractedText(''); }} className="px-6 py-2 border border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors">
                Cancel
              </button>
            </div>
          </div>
        </form>
      )}

      {!showForm && (
        <button
          onClick={() => setShowForm(true)}
          className="flex items-center gap-2 px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 transition-colors mb-6"
        >
          <Plus className="w-5 h-5" />
          Add Chapter
        </button>
      )}

      <DndContext sensors={sensors} collisionDetection={closestCenter} onDragEnd={handleDragEnd}>
        <SortableContext items={project.chapters?.map(c => c.id) || []} strategy={verticalListSortingStrategy}>
          <div className="space-y-4">
            {project.chapters?.map((chapter) => (
              <SortableChapter key={chapter.id} chapter={chapter} projectId={project.id} />
            ))}
          </div>
        </SortableContext>
      </DndContext>

      <ExportModal
        isOpen={showExportModal}
        onClose={() => setShowExportModal(false)}
        onExport={handleExport}
        isExporting={isExporting}
      />

      {showOneClickModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white dark:bg-gray-800 rounded-xl p-6 shadow-xl max-w-md w-full">
            <h2 className="text-xl font-bold text-gray-900 dark:text-white mb-4">Generate Entire Audiobook</h2>
            <p className="text-sm text-gray-600 dark:text-gray-400 mb-4">
              This will automatically extract text, split into chapters, generate audio for all chapters, and export the final audiobook.
            </p>
            <div className="space-y-4 mb-6">
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Voice</label>
                <select
                  value={selectedVoice}
                  onChange={(e) => setSelectedVoice(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                >
                  {voices.map((voice) => (
                    <option key={voice.id} value={voice.id}>{voice.name}</option>
                  ))}
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Format</label>
                <select className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white">
                  <option value="mp3">MP3</option>
                  <option value="wav">WAV</option>
                  <option value="flac">FLAC</option>
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Quality</label>
                <select className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white">
                  <option value="128k">128 kbps</option>
                  <option value="192k" selected>192 kbps</option>
                  <option value="320k">320 kbps</option>
                </select>
              </div>
            </div>
            <div className="flex gap-2">
              <button
                onClick={handleOneClickGenerate}
                disabled={!selectedVoice}
                className="flex-1 px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition-colors disabled:opacity-50"
              >
                Generate Audiobook
              </button>
              <button
                onClick={() => setShowOneClickModal(false)}
                className="px-4 py-2 border border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors"
              >
                Cancel
              </button>
            </div>
          </div>
        </div>
      )}

      {isGenerating && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white dark:bg-gray-800 rounded-xl p-6 shadow-xl max-w-md w-full">
            <h2 className="text-xl font-bold text-gray-900 dark:text-white mb-4">Generating Audiobook</h2>
            <div className="mb-4">
              <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2">
                <div
                  className="bg-purple-600 h-2 rounded-full transition-all"
                  style={{ width: `${generationProgress}%` }}
                />
              </div>
              <p className="text-sm text-gray-600 dark:text-gray-400 mt-2">{generationStatus} - {generationProgress}%</p>
            </div>
            <p className="text-xs text-gray-500 dark:text-gray-400">
              Please wait while we extract, split, generate audio, and export your audiobook.
            </p>
          </div>
        </div>
      )}
    </div>
  )
}
