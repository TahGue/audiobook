import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { api } from '../lib/api'

// Types
export interface TTSJobRequest {
  chapter_id: string
  voice_id: string
  language?: string
  priority?: number
}

export interface TTSJobResponse {
  job_id: string
  chapter_id: string
  status: 'pending' | 'processing' | 'completed' | 'failed' | 'cancelled'
  progress: number
  output_path?: string
  error_message?: string
  created_at: string
  completed_at?: string
  estimated_duration?: number
}

export interface JobStatusResponse {
  job_id: string
  status: string
  progress: number
  message: string
}

export interface QueueStats {
  available: boolean
  pending: number
  processing: number
  completed: number
  failed: number
  total: number
  message?: string
}

// Query keys
export const jobKeys = {
  all: ['jobs'] as const,
  status: (jobId: string) => [...jobKeys.all, 'status', jobId] as const,
  result: (jobId: string) => [...jobKeys.all, 'result', jobId] as const,
  stats: () => [...jobKeys.all, 'stats'] as const,
}

// API functions
const jobsApi = {
  enqueue: async (data: TTSJobRequest): Promise<TTSJobResponse> => {
    const response = await api.post('/jobs/tts/enqueue', data)
    return response.data
  },
  
  getStatus: async (jobId: string): Promise<JobStatusResponse> => {
    const response = await api.get(`/jobs/tts/${jobId}/status`)
    return response.data
  },
  
  getResult: async (jobId: string): Promise<TTSJobResponse> => {
    const response = await api.get(`/jobs/tts/${jobId}/result`)
    return response.data
  },
  
  cancel: async (jobId: string): Promise<{ success: boolean; message: string }> => {
    const response = await api.post(`/jobs/tts/${jobId}/cancel`)
    return response.data
  },
  
  getStats: async (): Promise<QueueStats> => {
    const response = await api.get('/jobs/queue/stats')
    return response.data
  },
}

// Hooks
export function useEnqueueTTSJob() {
  const queryClient = useQueryClient()
  
  return useMutation({
    mutationFn: jobsApi.enqueue,
    onSuccess: (data) => {
      // Start polling for job status
      queryClient.invalidateQueries({ queryKey: jobKeys.status(data.job_id) })
    },
  })
}

export function useJobStatus(jobId: string, enabled: boolean = true) {
  return useQuery({
    queryKey: jobKeys.status(jobId),
    queryFn: () => jobsApi.getStatus(jobId),
    enabled: enabled && !!jobId,
    refetchInterval: (query) => {
      const data = query.state.data as JobStatusResponse | undefined
      // Poll every 2 seconds while processing, stop when completed/failed
      if (data?.status === 'processing' || data?.status === 'pending') {
        return 2000
      }
      return false
    },
  })
}

export function useJobResult(jobId: string, enabled: boolean = true) {
  return useQuery({
    queryKey: jobKeys.result(jobId),
    queryFn: () => jobsApi.getResult(jobId),
    enabled: enabled && !!jobId,
  })
}

export function useCancelJob() {
  const queryClient = useQueryClient()
  
  return useMutation({
    mutationFn: jobsApi.cancel,
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: jobKeys.status(variables) })
    },
  })
}

export function useQueueStats(enabled: boolean = true) {
  return useQuery({
    queryKey: jobKeys.stats(),
    queryFn: jobsApi.getStats,
    enabled,
    refetchInterval: 5000, // Poll every 5 seconds
  })
}

// Convenience hook for full job lifecycle
export function useTTSJob() {
  const enqueue = useEnqueueTTSJob()
  const cancel = useCancelJob()
  const queryClient = useQueryClient()
  
  const startJob = async (request: TTSJobRequest) => {
    const result = await enqueue.mutateAsync(request)
    return result.job_id
  }
  
  const cancelJob = async (jobId: string) => {
    await cancel.mutateAsync(jobId)
  }
  
  const refreshJob = (jobId: string) => {
    queryClient.invalidateQueries({ queryKey: jobKeys.status(jobId) })
    queryClient.invalidateQueries({ queryKey: jobKeys.result(jobId) })
  }
  
  return {
    startJob,
    cancelJob,
    refreshJob,
    isEnqueuing: enqueue.isPending,
    isCancelling: cancel.isPending,
    enqueueError: enqueue.error,
    cancelError: cancel.error,
  }
}
