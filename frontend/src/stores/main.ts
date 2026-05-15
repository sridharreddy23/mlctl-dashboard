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

  // API base URL
  const api = axios.create({
    baseURL: '/api'
  })

  // Clear messages
  const clearMessages = () => {
    error.value = null
    successMessage.value = null
  }

  // Fetch config
  const fetchConfig = async () => {
    try {
      const response = await api.get('/config')
      config.value = response.data
      return config.value
    } catch (err: any) {
      error.value = err.message
      throw err
    }
  }

  // Update config
  const updateConfig = async (newConfig: any) => {
    try {
      loading.value = true
      const response = await api.post('/config', newConfig)
      config.value = response.data
      successMessage.value = 'Configuration updated successfully'
      return response.data
    } catch (err: any) {
      error.value = err.response?.data?.detail || err.message
      throw err
    } finally {
      loading.value = false
    }
  }

  // Fetch channels
  const fetchChannels = async () => {
    try {
      loading.value = true
      const response = await api.get('/channels')
      channels.value = response.data
      return channels.value
    } catch (err: any) {
      error.value = err.response?.data?.detail || err.message
      throw err
    } finally {
      loading.value = false
    }
  }

  // Fetch jobs
  const fetchJobs = async () => {
    try {
      const response = await api.get('/jobs')
      jobs.value = response.data
      return jobs.value
    } catch (err: any) {
      error.value = err.response?.data?.detail || err.message
      throw err
    }
  }

  // Get single job
  const getJob = async (jobId: string) => {
    try {
      const response = await api.get(`/jobs/${jobId}`)
      const index = jobs.value.findIndex(j => j.id === jobId)
      if (index >= 0) {
        jobs.value[index] = response.data
      }
      return response.data
    } catch (err: any) {
      error.value = err.response?.data?.detail || err.message
      throw err
    }
  }

  // Schedule restart
  const scheduleRestart = async (channelName: string, arn: string, scheduledTime: string, timezone: string) => {
    try {
      loading.value = true
      clearMessages()
      const response = await api.post('/schedule', {
        channel_name: channelName,
        arn,
        scheduled_time: scheduledTime,
        timezone
      })
      successMessage.value = `Job scheduled: ${response.data.job_id}`
      await fetchJobs()
      return response.data
    } catch (err: any) {
      error.value = err.response?.data?.detail || err.message
      throw err
    } finally {
      loading.value = false
    }
  }

  // Cancel job
  const cancelJob = async (jobId: string) => {
    try {
      loading.value = true
      clearMessages()
      await api.post(`/jobs/${jobId}/cancel`)
      successMessage.value = `Job ${jobId} cancelled`
      await fetchJobs()
    } catch (err: any) {
      error.value = err.response?.data?.detail || err.message
      throw err
    } finally {
      loading.value = false
    }
  }

  // Get job logs
  const getJobLogs = async (jobId: string): Promise<string> => {
    try {
      const response = await api.get(`/jobs/${jobId}/logs`)
      return response.data.logs || 'No logs available'
    } catch (err: any) {
      error.value = err.response?.data?.detail || err.message
      return 'Failed to load logs'
    }
  }

  // Get channel status
  const getChannelStatus = async (arn: string): Promise<string> => {
    try {
      const response = await api.get(`/status/${encodeURIComponent(arn)}`)
      return response.data.status
    } catch (err: any) {
      return 'UNKNOWN'
    }
  }

  const fetchAwsCredentials = async () => {
    try {
      const response = await api.get('/medialive/aws-credentials')
      awsCredentials.value = response.data
      return awsCredentials.value
    } catch (err: any) {
      error.value = err.response?.data?.detail || err.message
      throw err
    }
  }

  const updateAwsCredentials = async (credentials: any) => {
    try {
      loading.value = true
      clearMessages()
      const response = await api.post('/medialive/aws-credentials', credentials)
      awsCredentials.value = response.data
      successMessage.value = 'AWS credentials exported for MediaLive add-on'
      return response.data
    } catch (err: any) {
      error.value = err.response?.data?.detail || err.message
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
      error.value = err.response?.data?.detail || err.message
      throw err
    }
  }

  const fetchMediaLiveChannels = async () => {
    try {
      const response = await api.get('/medialive/channels')
      medialiveChannels.value = response.data
      return medialiveChannels.value
    } catch (err: any) {
      error.value = err.response?.data?.detail || err.message
      throw err
    }
  }

  const getMediaLiveInputDetails = async (payload: any) => {
    try {
      loading.value = true
      const response = await api.post('/medialive/input-details', payload)
      return response.data
    } catch (err: any) {
      error.value = err.response?.data?.detail || err.message
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
    } catch (err: any) {
      error.value = err.response?.data?.detail || err.message
      throw err
    }
  }

  const scheduleMediaLiveInputUrl = async (payload: any) => {
    try {
      loading.value = true
      clearMessages()
      const response = await api.post('/medialive/schedule-input-url', payload)
      successMessage.value = `MediaLive input job scheduled: ${response.data.job_id}`
      await fetchMediaLiveJobs()
      return response.data
    } catch (err: any) {
      error.value = err.response?.data?.detail || err.message
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
      successMessage.value = `MediaLive input job ${jobId} cancelled`
      await fetchMediaLiveJobs()
    } catch (err: any) {
      error.value = err.response?.data?.detail || err.message
      throw err
    } finally {
      loading.value = false
    }
  }

  const getMediaLiveJobLogs = async (jobId: string): Promise<string> => {
    try {
      const response = await api.get(`/medialive/jobs/${jobId}/logs`)
      return response.data.logs || 'No logs available'
    } catch (err: any) {
      error.value = err.response?.data?.detail || err.message
      return 'Failed to load logs'
    }
  }

  const activeJobs = computed(() => jobs.value.filter(j => j.status === 'waiting' || j.status === 'running'))
  const completedJobs = computed(() => jobs.value.filter(j => j.status === 'done' || j.status === 'failed' || j.status === 'cancelled'))
  const activeMediaLiveJobs = computed(() => medialiveJobs.value.filter(j => j.status === 'waiting' || j.status === 'running'))

  return {
    jobs,
    channels,
    config,
    awsCredentials,
    medialiveChannels,
    medialiveJobs,
    loading,
    error,
    successMessage,
    activeJobs,
    completedJobs,
    clearMessages,
    fetchConfig,
    updateConfig,
    fetchChannels,
    fetchJobs,
    getJob,
    scheduleRestart,
    cancelJob,
    getJobLogs,
    getChannelStatus,
    fetchAwsCredentials,
    updateAwsCredentials,
    getAwsExportCommands,
    fetchMediaLiveChannels,
    getMediaLiveInputDetails,
    fetchMediaLiveJobs,
    scheduleMediaLiveInputUrl,
    cancelMediaLiveJob,
    getMediaLiveJobLogs,
    activeMediaLiveJobs,
    api
  }
})
