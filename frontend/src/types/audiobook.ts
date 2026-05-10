export interface Project {
  id: string
  title: string
  description: string | null
  language: string
  created_at: string
  updated_at: string
  chapter_count?: number
  chapters?: Chapter[]
}

export interface Chapter {
  id: string
  project_id: string
  title: string
  content: string
  language: string
  voice_id: string | null
  audio_path: string | null
  duration_seconds: number | null
  order_index: number
  created_at: string
  updated_at: string
}

export interface Voice {
  id: string
  name: string
  gender: 'male' | 'female'
}

export interface Language {
  code: string
  name: string
}

export interface PageText {
  page: number
  text: string
}

export interface PDFExtractResponse {
  pages: PageText[]
  total_pages: number
  total_chars: number
  full_text: string
}
