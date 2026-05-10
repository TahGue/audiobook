import axios from 'axios'
import { Project, Chapter, Voice, Language, PDFExtractResponse } from '../types/audiobook'

export const api = axios.create({
  baseURL: '/api',
  headers: { 'Content-Type': 'application/json' },
})

export const projectsApi = {
  list: () => api.get<Project[]>('/projects/').then(r => r.data),
  create: (data: { title: string; description?: string; language?: string }) =>
    api.post<Project>('/projects/', data).then(r => r.data),
  get: (id: string) => api.get<Project>(`/projects/${id}/`).then(r => r.data),
  update: (id: string, data: Partial<Project>) =>
    api.patch<Project>(`/projects/${id}/`, data).then(r => r.data),
  delete: (id: string) => api.delete(`/projects/${id}/`),
}

export const chaptersApi = {
  list: (projectId: string) =>
    api.get<Chapter[]>(`/chapters/?project_id=${projectId}`).then(r => r.data),
  create: (data: { title: string; content: string; project_id: string; language?: string }) =>
    api.post<Chapter>('/chapters/', data).then(r => r.data),
  get: (id: string) => api.get<Chapter>(`/chapters/${id}/`).then(r => r.data),
  update: (id: string, data: Partial<Chapter>) =>
    api.patch<Chapter>(`/chapters/${id}/`, data).then(r => r.data),
  delete: (id: string) => api.delete(`/chapters/${id}/`),
  reorder: (id: string, orderIndex: number) =>
    api.patch(`/chapters/${id}/reorder/`, null, { params: { order_index: orderIndex } }),
}

export const ttsApi = {
  getLanguages: () => api.get<Language[]>('/tts/languages/').then(r => r.data),
  getVoices: (language: string) => api.get<Voice[]>('/tts/voices/', { params: { language } }).then(r => r.data),
  generate: (data: { chapter_id: string; voice_id: string; language: string }) =>
    api.post('/tts/generate/', data).then(r => r.data),
}

export const pdfApi = {
  extract: async (file: File, onProgress?: (progress: number) => void): Promise<PDFExtractResponse> => {
    const formData = new FormData()
    formData.append('file', file)
    const response = await api.post<PDFExtractResponse>('/pdf/extract/', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
      onUploadProgress: (progressEvent) => {
        if (progressEvent.total && onProgress) {
          const percentCompleted = Math.round((progressEvent.loaded * 100) / progressEvent.total)
          onProgress(percentCompleted)
        }
      },
    })
    return response.data
  },
  ocr: async (file: File, language: string = 'ar', onProgress?: (progress: number) => void): Promise<PDFExtractResponse> => {
    const formData = new FormData()
    formData.append('file', file)
    const response = await api.post<PDFExtractResponse>('/pdf/ocr/', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
      params: { language },
      onUploadProgress: (progressEvent) => {
        if (progressEvent.total && onProgress) {
          const percentCompleted = Math.round((progressEvent.loaded * 100) / progressEvent.total)
          onProgress(percentCompleted)
        }
      },
    })
    return response.data
  },
}

export interface DocumentExtractResponse {
  text: string
  total_chars: number
  file_type: string
  file_name: string
  cached: boolean
}

export const documentsApi = {
  extract: async (file: File, onProgress?: (progress: number) => void): Promise<DocumentExtractResponse> => {
    const formData = new FormData()
    formData.append('file', file)
    const response = await api.post<DocumentExtractResponse>('/documents/extract/', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
      onUploadProgress: (progressEvent) => {
        if (progressEvent.total && onProgress) {
          const percentCompleted = Math.round((progressEvent.loaded * 100) / progressEvent.total)
          onProgress(percentCompleted)
        }
      },
    })
    return response.data
  },
  getSupportedFormats: () => api.get('/documents/supported-formats/').then(r => r.data),
}

export const exportApi = {
  exportProject: (projectId: string, format: 'mp3' | 'wav' | 'flac' = 'mp3', quality: '128k' | '192k' | '320k' = '192k') =>
    api.post(`/export/${projectId}/`, { format, quality }, { responseType: 'blob' }),
}

export const arabicApi = {
  process: async (text: string, addDiacritics: boolean = true) => {
    const response = await api.post('/arabic/process/', { text, add_diacritics: addDiacritics })
    return response.data
  },
  diacritize: async (text: string) => {
    const response = await api.post('/arabic/diacritize/', { text })
    return response.data
  },
}
