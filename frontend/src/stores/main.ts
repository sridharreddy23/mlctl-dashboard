import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import axios from 'axios'

export interface Job {
  id: string
  name: string
  arn: string
  status: string
  time: string
  time_until: string
  pid?: number
}

export interface Channel {
  name: string
  arn: string
}

export interface Config {
  configured: boolean
  base_url?: string
  blip_domain?: string
  has_client_id: boolean
  has_client_secret: boolean
}

export interface AwsCredentialStatus {
  configured: boolean
  region: string
  has_access_key: boolean
  has_secret_key: boolean
  has_session_token: boolean
  access_key_preview?: string
  exported_at?: string
}

export interface MediaLiveJob {
  id: string
  name: string
  arn: string
  mode: string
  target_url: string
  status: string
  time: string
  time_until: string
  pid?: number
}

export interface Toast {
  id: number
  message: string
  type: 'success' | 'error' | 'warning' | 'info'
}

export interface ChannelStatusItem {
  name: string
  arn: string
  status: string
  error?: string | null
}

export interface ChannelStatusResult {
  configured?: boolean
  channels: ChannelStatusItem[]
  message?: string | null
}

let toastIdCounter = 0

export const useStore = defineStore('main', () => {
  const jobs = ref<Job[]>([])
  const channels = ref<Channel[]>([])
  const config = ref<Config | null>(null)
  const awsCredentials = ref<AwsCredentialStatus | null>(null)
  const medialiveChannels = ref<Channel[]>([])
  const medialiveJobs = ref<MediaLiveJob[]>([])
  const loading = ref(false)
  const error = ref<string | null>(null)
  const successMessage = ref<string | null>(null)
  const toasts = ref<Toast[]>([])

  const api = axios.create({ baseURL: '/api' })

  // ================= TOAST SYSTEM =================

  const addToast = (message: string, type: Toast['type'] = 'info', durationMs = 5000) => {
    const id = ++toastIdCounter
    toasts.value.push({ id, message, type })
    if (durationMs > 0) {
      setTimeout(() => removeToast(id), durationMs)
    }
  }

  const removeToast = (id: number) => {
    toasts.value = toasts.value.filter(t => t.id !== id)
  }

  // ================= MESSAGES =================

  const clearMessages = () => {
    error.value = null
    successMessage.value = null
  }

  const setError = (msg: string) => {
    error.value = msg
    addToast(msg, 'error')
  }

  const setSuccess = (msg: string) => {
    successMessage.value = msg
    addToast(msg, 'success')
  }

  // ================= CONFIG =================

  const fetchConfig = async () => {
    try {
      const response = await api.get('/config')
      config.value = response.data
      return config.value
    } catch (err: any) {
      setError(err.message)
      throw err
    }
  }

  const updateConfig = async (newConfig: any) => {
    try {
      loading.value = true
      const response = await api.post('/config', newConfig)
      config.value = response.data
      setSuccess('Configuration updated successfully')
      return response.data
    } catch (err: any) {
      setError(err.response?.data?.detail || err.message)
      throw err
    } finally {
      loading.value = false
    }
  }

  // ================= CHANNELS =================

  const fetchChannels = async () => {
    try {
      loading.value = true
      const response = await api.get('/channels')
      channels.value = response.data
      return channels.value
    } catch (err: any) {
      setError(err.response?.data?.detail || err.message)
      throw err
    } finally {
      loading.value = false
    }
  }

  // ================= JOBS =================

  const fetchJobs = async () => {
    try {
      const response = await api.get('/jobs')
      jobs.value = response.data
      return jobs.value
    } catch {
      // Silent — background poll should not show errors
    }
  }

  const getJob = async (jobId: string) => {
    try {
      const response = await api.get(`/jobs/${jobId}`)
      const index = jobs.value.findIndex(j => j.id === jobId)
      if (index >= 0) jobs.value[index] = response.data
      return response.data
    } catch (err: any) {
      setError(err.response?.data?.detail || err.message)
      throw err
    }
  }

  const scheduleRestart = async (channelName: string, arn: string, scheduledTime: string, timezone: string) => {
    try {
      loading.value = true
      clearMessages()
      const response = await api.post('/schedule', { channel_name: channelName, arn, scheduled_time: scheduledTime, timezone })
      setSuccess(`Job scheduled: ${response.data.job_id}`)
      await fetchJobs()
      return response.data
    } catch (err: any) {
      setError(err.response?.data?.detail || err.message)
      throw err
    } finally {
      loading.value = false
    }
  }

  const cancelJob = async (jobId: string) => {
    try {
      loading.value = true
      clearMessages()
      await api.post(`/jobs/${jobId}/cancel`)
      setSuccess(`Job ${jobId} cancelled`)
      await fetchJobs()
    } catch (err: any) {
      setError(err.response?.data?.detail || err.message)
      throw err
    } finally {
      loading.value = false
    }
  }

  const checkHealth = async (): Promise<{ status: string; configured: boolean }> => {
    const response = await api.get('/health')
    return response.data
  }

  const fetchChannelStatuses = async (): Promise<ChannelStatusResult | ChannelStatusItem[]> => {
    const response = await api.get('/channels/status', { timeout: 120000 })
    return response.data
  }

  const retryJob = async (jobId: string) => {
    try {
      loading.value = true
      clearMessages()
      const response = await api.post(`/jobs/${jobId}/retry`)
      setSuccess(`Job rescheduled: ${response.data.job_id}`)
      await fetchJobs()
      return response.data
    } catch (err: any) {
      setError(err.response?.data?.detail || err.message)
      throw err
    } finally {
      loading.value = false
    }
  }

  const getJobLogs = async (jobId: string): Promise<string> => {
    try {
      const response = await api.get(`/jobs/${jobId}/logs`)
      return response.data.logs || 'No logs available'
    } catch (err: any) {
      return 'Failed to load logs'
    }
  }

  const getChannelStatus = async (arn: string): Promise<string> => {
    try {
      const response = await api.get(`/status/${encodeURIComponent(arn)}`)
      return response.data.status
    } catch {
      return 'UNKNOWN'
    }
  }

  // ================= PURGE =================

  const purgeJobs = async (days = 7) => {
    try {
      loading.value = true
      const response = await api.post('/jobs/purge', { days })
      setSuccess(`Purged ${response.data.removed} old jobs`)
      await fetchJobs()
      await fetchMediaLiveJobs()
      return response.data
    } catch (err: any) {
      setError(err.response?.data?.detail || err.message)
      throw err
    } finally {
      loading.value = false
    }
  }

  // ================= CSV EXPORT =================

  const exportJobsCSV = () => {
    const allJobs = [...jobs.value, ...medialiveJobs.value]
    const headers = ['ID', 'Name', 'ARN', 'Status', 'Scheduled Time', 'Time Until']
    const rows = allJobs.map(j => [
      j.id,
      `"${(j.name || '').replace(/"/g, '""')}"`,
      `"${j.arn}"`,
      j.status,
      j.time,
      j.time_until
    ])
    const csv = [headers.join(','), ...rows.map(r => r.join(','))].join('\n')
    const blob = new Blob([csv], { type: 'text/csv' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `mlctl-jobs-${new Date().toISOString().slice(0, 10)}.csv`
    a.click()
    URL.revokeObjectURL(url)
    addToast('Jobs exported as CSV', 'info', 3000)
  }

  // ================= AWS CREDENTIALS =================

  const fetchAwsCredentials = async () => {
    try {
      const response = await api.get('/medialive/aws-credentials')
      awsCredentials.value = response.data
      return awsCredentials.value
    } catch (err: any) {
      setError(err.response?.data?.detail || err.message)
      throw err
    }
  }

  const updateAwsCredentials = async (credentials: any) => {
    try {
      loading.value = true
      clearMessages()
      const response = await api.post('/medialive/aws-credentials', credentials)
      awsCredentials.value = response.data
      setSuccess('AWS credentials exported for MediaLive add-on')
      return response.data
    } catch (err: any) {
      setError(err.response?.data?.detail || err.message)
      throw err
    } finally {
      loading.value = false
    }
  }

  const getAwsExportCommands = async (): Promise<string> => {
    try {
      const response = await api.get('/medialive/aws-credentials/export')
      return response.data.commands
    } catch (err: any) {
      setError(err.response?.data?.detail || err.message)
      throw err
    }
  }

  // ================= MEDIALIVE =================

  const fetchMediaLiveChannels = async () => {
    try {
      const response = await api.get('/medialive/channels')
      medialiveChannels.value = response.data
      return medialiveChannels.value
    } catch (err: any) {
      setError(err.response?.data?.detail || err.message)
      throw err
    }
  }

  const getMediaLiveInputDetails = async (payload: any) => {
    try {
      loading.value = true
      const response = await api.post('/medialive/input-details', payload)
      return response.data
    } catch (err: any) {
      setError(err.response?.data?.detail || err.message)
      throw err
    } finally {
      loading.value = false
    }
  }

  const fetchMediaLiveJobs = async () => {
    try {
      const response = await api.get('/medialive/jobs')
      medialiveJobs.value = response.data
      return medialiveJobs.value
    } catch {
      // Silent — background poll
    }
  }

  const scheduleMediaLiveInputUrl = async (payload: any) => {
    try {
      loading.value = true
      clearMessages()
      const response = await api.post('/medialive/schedule-input-url', payload)
      setSuccess(`MediaLive input job scheduled: ${response.data.job_id}`)
      await fetchMediaLiveJobs()
      return response.data
    } catch (err: any) {
      setError(err.response?.data?.detail || err.message)
      throw err
    } finally {
      loading.value = false
    }
  }

  const cancelMediaLiveJob = async (jobId: string) => {
    try {
      loading.value = true
      clearMessages()
      await api.post(`/medialive/jobs/${jobId}/cancel`)
      setSuccess(`MediaLive input job ${jobId} cancelled`)
      await fetchMediaLiveJobs()
    } catch (err: any) {
      setError(err.response?.data?.detail || err.message)
      throw err
    } finally {
      loading.value = false
    }
  }

  const getMediaLiveJobLogs = async (jobId: string): Promise<string> => {
    try {
      const response = await api.get(`/medialive/jobs/${jobId}/logs`)
      return response.data.logs || 'No logs available'
    } catch {
      return 'Failed to load logs'
    }
  }

  // ================= COMPUTED =================

  const activeJobs = computed(() => jobs.value.filter(j => j.status === 'waiting' || j.status === 'running'))
  const completedJobs = computed(() => jobs.value.filter(j => j.status === 'done' || j.status === 'failed' || j.status === 'cancelled'))
  const activeMediaLiveJobs = computed(() => medialiveJobs.value.filter(j => j.status === 'waiting' || j.status === 'running'))

  return {
    jobs, channels, config, awsCredentials, medialiveChannels, medialiveJobs,
    loading, error, successMessage, toasts,
    activeJobs, completedJobs, activeMediaLiveJobs,
    addToast, removeToast, clearMessages,
    fetchConfig, updateConfig, fetchChannels,
    fetchJobs, getJob, scheduleRestart, cancelJob, retryJob, checkHealth, fetchChannelStatuses, getJobLogs, getChannelStatus,
    purgeJobs, exportJobsCSV,
    fetchAwsCredentials, updateAwsCredentials, getAwsExportCommands,
    fetchMediaLiveChannels, getMediaLiveInputDetails,
    fetchMediaLiveJobs, scheduleMediaLiveInputUrl, cancelMediaLiveJob, getMediaLiveJobLogs,
  }
})
