import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { projectsApi, chaptersApi } from '../lib/api'
import { Project, Chapter } from '../types/audiobook'

// Query keys
export const projectKeys = {
  all: ['projects'] as const,
  lists: () => [...projectKeys.all, 'list'] as const,
  list: (filters: object) => [...projectKeys.lists(), { filters }] as const,
  details: () => [...projectKeys.all, 'detail'] as const,
  detail: (id: string) => [...projectKeys.details(), id] as const,
}

export const chapterKeys = {
  all: ['chapters'] as const,
  lists: () => [...chapterKeys.all, 'list'] as const,
  list: (projectId: string) => [...chapterKeys.lists(), { projectId }] as const,
  details: () => [...chapterKeys.all, 'detail'] as const,
  detail: (id: string) => [...chapterKeys.details(), id] as const,
}

// Project hooks
export function useProjects() {
  return useQuery({
    queryKey: projectKeys.lists(),
    queryFn: projectsApi.list,
  })
}

export function useProject(id: string) {
  return useQuery({
    queryKey: projectKeys.detail(id),
    queryFn: () => projectsApi.get(id),
    enabled: !!id,
  })
}

export function useCreateProject() {
  const queryClient = useQueryClient()
  
  return useMutation({
    mutationFn: projectsApi.create,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: projectKeys.lists() })
    },
  })
}

export function useUpdateProject() {
  const queryClient = useQueryClient()
  
  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: Partial<Project> }) =>
      projectsApi.update(id, data),
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: projectKeys.detail(data.id) })
      queryClient.invalidateQueries({ queryKey: projectKeys.lists() })
    },
  })
}

export function useDeleteProject() {
  const queryClient = useQueryClient()
  
  return useMutation({
    mutationFn: projectsApi.delete,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: projectKeys.lists() })
    },
  })
}

// Chapter hooks
export function useChapters(projectId: string) {
  return useQuery({
    queryKey: chapterKeys.list(projectId),
    queryFn: () => chaptersApi.list(projectId),
    enabled: !!projectId,
  })
}

export function useChapter(id: string) {
  return useQuery({
    queryKey: chapterKeys.detail(id),
    queryFn: () => chaptersApi.get(id),
    enabled: !!id,
  })
}

export function useCreateChapter() {
  const queryClient = useQueryClient()
  
  return useMutation({
    mutationFn: chaptersApi.create,
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: chapterKeys.list(data.project_id) })
    },
  })
}

export function useUpdateChapter() {
  const queryClient = useQueryClient()
  
  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: Partial<Chapter> }) =>
      chaptersApi.update(id, data),
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: chapterKeys.detail(data.id) })
      queryClient.invalidateQueries({ queryKey: chapterKeys.list(data.project_id) })
    },
  })
}

export function useDeleteChapter() {
  const queryClient = useQueryClient()
  
  return useMutation({
    mutationFn: ({ id, projectId }: { id: string; projectId: string }) =>
      chaptersApi.delete(id).then(() => ({ id, projectId })),
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: chapterKeys.list(data.projectId) })
    },
  })
}
