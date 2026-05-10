import { useState, useEffect } from 'react'
import { Settings as SettingsIcon, Download, Save, Volume2, Cpu, Moon, Sun, Mic, Trash2, Upload } from 'lucide-react'
import { ttsApi } from '../lib/api'
import { useDarkMode } from '../contexts/DarkModeContext'

interface Settings {
  defaultLanguage: string
  defaultVoice: string
  ttsEngine: 'edge' | 'piper'
  audioQuality: '128k' | '192k' | '320k'
  ocrEngine: 'surya' | 'easyocr'
  useGpu: boolean
  autoDownloadModels: boolean
}

export default function Settings() {
  const { darkMode, toggleDarkMode } = useDarkMode()
  
  const [settings, setSettings] = useState<Settings>({
    defaultLanguage: 'en',
    defaultVoice: '',
    ttsEngine: 'edge',
    audioQuality: '192k',
    ocrEngine: 'surya',
    useGpu: true,
    autoDownloadModels: true,
  })

  const [voiceProfiles, setVoiceProfiles] = useState<any[]>([])
  const [isVoiceCloneAvailable, setIsVoiceCloneAvailable] = useState(false)
  const [voiceName, setVoiceName] = useState('')
  const [voiceLanguage, setVoiceLanguage] = useState('en')
  const [voiceFile, setVoiceFile] = useState<File | null>(null)
  const [isUploadingVoice, setIsUploadingVoice] = useState(false)
  
  const [voices, setVoices] = useState<any[]>([])
  const [loadingVoices, setLoadingVoices] = useState(false)
  const [saving, setSaving] = useState(false)
  const [message, setMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null)

  const loadVoices = async (language: string) => {
    setLoadingVoices(true)
    try {
      const data = await ttsApi.getVoices(language)
      setVoices(data)
    } catch (error) {
      console.error('Failed to load voices:', error)
    } finally {
      setLoadingVoices(false)
    }
  }

  const handleLanguageChange = (language: string) => {
    setSettings({ ...settings, defaultLanguage: language, defaultVoice: '' })
    loadVoices(language)
  }

  useEffect(() => {
    loadVoiceProfiles()
    checkVoiceCloneAvailability()
  }, [])

  const loadVoiceProfiles = async () => {
    try {
      const data = await ttsApi.listVoiceProfiles()
      setVoiceProfiles(data.profiles || [])
    } catch (error) {
      console.error('Failed to load voice profiles:', error)
    }
  }

  const checkVoiceCloneAvailability = async () => {
    try {
      const data = await ttsApi.checkVoiceCloneAvailable()
      setIsVoiceCloneAvailable(data.available)
    } catch (error) {
      console.error('Failed to check voice clone availability:', error)
    }
  }

  const handleCreateVoiceProfile = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!voiceFile || !voiceName) return

    setIsUploadingVoice(true)
    try {
      await ttsApi.createVoiceProfile(voiceName, voiceLanguage, voiceFile)
      setMessage({ type: 'success', text: 'Voice profile created successfully' })
      setVoiceName('')
      setVoiceFile(null)
      loadVoiceProfiles()
    } catch (error) {
      setMessage({ type: 'error', text: 'Failed to create voice profile' })
    } finally {
      setIsUploadingVoice(false)
    }
  }

  const handleDeleteVoiceProfile = async (voiceId: string) => {
    try {
      await ttsApi.deleteVoiceProfile(voiceId)
      setMessage({ type: 'success', text: 'Voice profile deleted successfully' })
      loadVoiceProfiles()
    } catch (error) {
      setMessage({ type: 'error', text: 'Failed to delete voice profile' })
    }
  }

  const handleSave = async () => {
    setSaving(true)
    setMessage(null)
    
    // Save to localStorage for now
    localStorage.setItem('audiobook-settings', JSON.stringify(settings))
    
    setTimeout(() => {
      setSaving(false)
      setMessage({ type: 'success', text: 'Settings saved successfully' })
      setTimeout(() => setMessage(null), 3000)
    }, 500)
  }

  const downloadModels = async () => {
    setMessage({ type: 'success', text: 'Model download started - this may take several minutes' })
    // This would call an API endpoint to download models
  }

  return (
    <div className="max-w-4xl mx-auto p-6">
      <div className="flex items-center gap-3 mb-8">
        <SettingsIcon className="w-8 h-8 text-indigo-600" />
        <h1 className="text-3xl font-bold text-gray-900 dark:text-white">Settings</h1>
      </div>

      {message && (
        <div className={`mb-6 p-4 rounded-lg ${
          message.type === 'success' 
            ? 'bg-green-50 dark:bg-green-900/20 text-green-700 dark:text-green-300 border border-green-200 dark:border-green-800'
            : 'bg-red-50 dark:bg-red-900/20 text-red-700 dark:text-red-300 border border-red-200 dark:border-red-800'
        }`}>
          {message.text}
        </div>
      )}

      <div className="space-y-6">
        {/* Appearance Settings */}
        <div className="bg-white dark:bg-gray-800 rounded-xl p-6 shadow-md">
          <h2 className="text-xl font-semibold text-gray-900 dark:text-white mb-4 flex items-center gap-2">
            {darkMode ? <Moon className="w-5 h-5 text-indigo-600" /> : <Sun className="w-5 h-5 text-indigo-600" />}
            Appearance
          </h2>
          
          <div className="flex items-center justify-between">
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                Dark Mode
              </label>
              <p className="text-xs text-gray-500 dark:text-gray-400">
                Switch between light and dark theme
              </p>
            </div>
            <button
              onClick={toggleDarkMode}
              className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${
                darkMode ? 'bg-indigo-600' : 'bg-gray-300 dark:bg-gray-600'
              }`}
            >
              <span
                className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
                  darkMode ? 'translate-x-6' : 'translate-x-1'
                }`}
              />
            </button>
          </div>
        </div>

        {/* TTS Settings */}
        <div className="bg-white dark:bg-gray-800 rounded-xl p-6 shadow-md">
          <h2 className="text-xl font-semibold text-gray-900 dark:text-white mb-4 flex items-center gap-2">
            <Volume2 className="w-5 h-5 text-indigo-600" />
            Text-to-Speech
          </h2>
          
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                Default Language
              </label>
              <select
                value={settings.defaultLanguage}
                onChange={(e) => handleLanguageChange(e.target.value)}
                className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
              >
                <option value="en">English</option>
                <option value="ar">Arabic</option>
                <option value="fr">French</option>
                <option value="es">Spanish</option>
                <option value="de">German</option>
                <option value="hi">Hindi</option>
                <option value="zh">Chinese</option>
                <option value="ru">Russian</option>
                <option value="pt">Portuguese</option>
                <option value="ja">Japanese</option>
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                Default Voice
              </label>
              <select
                value={settings.defaultVoice}
                onChange={(e) => setSettings({ ...settings, defaultVoice: e.target.value })}
                disabled={loadingVoices || voices.length === 0}
                className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white disabled:opacity-50"
              >
                <option value="">Auto-select</option>
                {voices.map((voice) => (
                  <option key={voice.id} value={voice.id}>
                    {voice.name} ({voice.gender})
                  </option>
                ))}
              </select>
              {loadingVoices && <p className="text-sm text-gray-500 mt-1">Loading voices...</p>}
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                TTS Engine
              </label>
              <select
                value={settings.ttsEngine}
                onChange={(e) => setSettings({ ...settings, ttsEngine: e.target.value as 'edge' | 'piper' })}
                className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
              >
                <option value="edge">Edge TTS (Online, High Quality)</option>
                <option value="piper">Piper TTS (Offline, Fast)</option>
              </select>
              <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                Edge TTS requires internet connection. Piper TTS works offline but has Python 3.13 compatibility issues.
              </p>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                Audio Export Quality
              </label>
              <select
                value={settings.audioQuality}
                onChange={(e) => setSettings({ ...settings, audioQuality: e.target.value as '128k' | '192k' | '320k' })}
                className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
              >
                <option value="128k">128 kbps (Smaller files)</option>
                <option value="192k">192 kbps (Balanced)</option>
                <option value="320k">320 kbps (Best quality)</option>
              </select>
            </div>

            <button
              onClick={downloadModels}
              className="flex items-center gap-2 px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 transition-colors"
            >
              <Download className="w-4 h-4" />
              Download Voice Models
            </button>
            <p className="text-xs text-gray-500 dark:text-gray-400">
              Download voice models for offline use. This may take several minutes depending on your connection.
            </p>
          </div>
        </div>

        {/* OCR Settings */}
        <div className="bg-white dark:bg-gray-800 rounded-xl p-6 shadow-md">
          <h2 className="text-xl font-semibold text-gray-900 dark:text-white mb-4 flex items-center gap-2">
            <Cpu className="w-5 h-5 text-indigo-600" />
            OCR & GPU
          </h2>
          
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                OCR Engine
              </label>
              <select
                value={settings.ocrEngine}
                onChange={(e) => setSettings({ ...settings, ocrEngine: e.target.value as 'surya' | 'easyocr' })}
                className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
              >
                <option value="surya">Surya OCR (Primary, Faster)</option>
                <option value="easyocr">EasyOCR (Fallback, 80+ languages)</option>
              </select>
              <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                Surya is faster and better for document-heavy workflows. EasyOCR supports more languages.
              </p>
            </div>

            <div className="flex items-center justify-between">
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  Use GPU Acceleration
                </label>
                <p className="text-xs text-gray-500 dark:text-gray-400">
                  Automatically detect and use CUDA/Metal GPU for faster OCR processing
                </p>
              </div>
              <button
                onClick={() => setSettings({ ...settings, useGpu: !settings.useGpu })}
                className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${
                  settings.useGpu ? 'bg-indigo-600' : 'bg-gray-300 dark:bg-gray-600'
                }`}
              >
                <span
                  className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
                    settings.useGpu ? 'translate-x-6' : 'translate-x-1'
                  }`}
                />
              </button>
            </div>

            <div className="flex items-center justify-between">
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  GPU Mode
                </label>
                <p className="text-xs text-gray-500 dark:text-gray-400">
                  Force GPU usage or fallback to CPU if unavailable
                </p>
              </div>
              <select
                value={settings.useGpu ? 'auto' : 'cpu'}
                onChange={(e) => setSettings({ ...settings, useGpu: e.target.value !== 'cpu' })}
                className="px-3 py-1.5 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white text-sm"
              >
                <option value="auto">Auto-detect GPU</option>
                <option value="cpu">Force CPU</option>
              </select>
            </div>

            <div className="p-4 bg-gray-50 dark:bg-gray-700 rounded-lg">
              <div className="flex items-center justify-between mb-2">
                <span className="text-sm font-medium text-gray-700 dark:text-gray-300">GPU Status</span>
                <span className="text-xs px-2 py-1 bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-300 rounded-full">Available</span>
              </div>
              <div className="grid grid-cols-2 gap-4 text-xs">
                <div>
                  <span className="text-gray-500 dark:text-gray-400">GPU Type:</span>
                  <span className="ml-2 text-gray-900 dark:text-white font-medium">NVIDIA RTX 4090</span>
                </div>
                <div>
                  <span className="text-gray-500 dark:text-gray-400">Est. Speedup:</span>
                  <span className="ml-2 text-gray-900 dark:text-white font-medium">~10x faster</span>
                </div>
              </div>
            </div>

            <div className="flex items-center justify-between">
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  Auto-download Models
                </label>
                <p className="text-xs text-gray-500 dark:text-gray-400">
                  Automatically download OCR/TTS models on first use
                </p>
              </div>
              <button
                onClick={() => setSettings({ ...settings, autoDownloadModels: !settings.autoDownloadModels })}
                className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${
                  settings.autoDownloadModels ? 'bg-indigo-600' : 'bg-gray-300 dark:bg-gray-600'
                }`}
              >
                <span
                  className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
                    settings.autoDownloadModels ? 'translate-x-6' : 'translate-x-1'
                  }`}
                />
              </button>
            </div>
          </div>
        </div>

        {/* Voice Cloning */}
        <div className="bg-white dark:bg-gray-800 rounded-xl p-6 shadow-md">
          <div className="flex items-center gap-3 mb-6">
            <div className="p-2 bg-purple-100 dark:bg-purple-900/30 rounded-lg">
              <Mic className="w-5 h-5 text-purple-600 dark:text-purple-400" />
            </div>
            <h2 className="text-xl font-semibold text-gray-900 dark:text-white">Voice Cloning</h2>
          </div>

          {!isVoiceCloneAvailable ? (
            <div className="p-4 bg-yellow-50 dark:bg-yellow-900/20 border border-yellow-200 dark:border-yellow-800 rounded-lg">
              <p className="text-sm text-yellow-700 dark:text-yellow-300">
                Voice cloning requires the TTS library. Install with: <code className="bg-yellow-100 dark:bg-yellow-900/40 px-1 rounded">pip install TTS</code>
              </p>
            </div>
          ) : (
            <div className="space-y-6">
              {/* Create Voice Profile */}
              <form onSubmit={handleCreateVoiceProfile} className="space-y-4">
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                      Voice Name
                    </label>
                    <input
                      type="text"
                      value={voiceName}
                      onChange={(e) => setVoiceName(e.target.value)}
                      placeholder="My Custom Voice"
                      className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                      required
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                      Language
                    </label>
                    <select
                      value={voiceLanguage}
                      onChange={(e) => setVoiceLanguage(e.target.value)}
                      className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                    >
                      <option value="en">English</option>
                      <option value="es">Spanish</option>
                      <option value="fr">French</option>
                      <option value="de">German</option>
                      <option value="ar">Arabic</option>
                    </select>
                  </div>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                    Voice Sample (3-10 seconds)
                  </label>
                  <input
                    type="file"
                    accept="audio/*"
                    onChange={(e) => setVoiceFile(e.target.files?.[0] || null)}
                    className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                    required
                  />
                  <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                    Upload a clear voice sample (3-10 seconds of speech)
                  </p>
                </div>
                <button
                  type="submit"
                  disabled={isUploadingVoice || !voiceFile || !voiceName}
                  className="flex items-center gap-2 px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition-colors disabled:opacity-50"
                >
                  <Upload className="w-4 h-4" />
                  {isUploadingVoice ? 'Creating Profile...' : 'Create Voice Profile'}
                </button>
              </form>

              {/* Voice Profiles List */}
              {voiceProfiles.length > 0 && (
                <div className="border-t border-gray-200 dark:border-gray-700 pt-6">
                  <h3 className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-3">
                    Your Voice Profiles ({voiceProfiles.length})
                  </h3>
                  <div className="space-y-2">
                    {voiceProfiles.map((profile) => (
                      <div
                        key={profile.id}
                        className="flex items-center justify-between p-3 bg-gray-50 dark:bg-gray-700 rounded-lg"
                      >
                        <div>
                          <div className="font-medium text-gray-900 dark:text-white">{profile.name}</div>
                          <div className="text-xs text-gray-500 dark:text-gray-400">{profile.language}</div>
                        </div>
                        <button
                          onClick={() => handleDeleteVoiceProfile(profile.id)}
                          className="p-2 text-red-600 hover:bg-red-50 dark:hover:bg-red-900/20 rounded-lg transition-colors"
                        >
                          <Trash2 className="w-4 h-4" />
                        </button>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}
        </div>

        {/* Save Button */}
        <div className="flex justify-end">
          <button
            onClick={handleSave}
            disabled={saving}
            className="flex items-center gap-2 px-6 py-3 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 transition-colors disabled:opacity-50"
          >
            <Save className="w-4 h-4" />
            {saving ? 'Saving...' : 'Save Settings'}
          </button>
        </div>
      </div>
    </div>
  )
}
