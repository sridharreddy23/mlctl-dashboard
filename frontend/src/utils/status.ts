/**
 * Shared status formatting and color utilities.
 * Used across DashboardView, ScheduleView, JobCard, JobsView, and MediaLiveInputView.
 */

/** Map a raw status string to a human-readable label. */
export const formatStatus = (status: string): string => {
  const map: Record<string, string> = {
    waiting: 'Waiting',
    running: 'Running',
    done: 'Done',
    failed: 'Failed',
    cancelled: 'Cancelled',
  }
  return map[status] || status
}

/** Tailwind text-color class for a status value. */
export const getStatusColor = (status: string): string => {
  const map: Record<string, string> = {
    waiting: 'text-yellow-600 dark:text-yellow-400',
    running: 'text-blue-600 dark:text-blue-400',
    done: 'text-green-600 dark:text-green-400',
    failed: 'text-red-600 dark:text-red-400',
    cancelled: 'text-slate-600 dark:text-slate-400',
  }
  return map[status] || ''
}

/** Tailwind background badge class for a status value. */
export const getStatusBgColor = (status: string): string => {
  const map: Record<string, string> = {
    done: 'bg-green-100 dark:bg-green-900 text-green-800 dark:text-green-200',
    failed: 'bg-red-100 dark:bg-red-900 text-red-800 dark:text-red-200',
    cancelled: 'bg-slate-100 dark:bg-slate-700 text-slate-800 dark:text-slate-200',
    waiting: 'bg-yellow-100 dark:bg-yellow-900 text-yellow-800 dark:text-yellow-200',
    running: 'bg-blue-100 dark:bg-blue-900 text-blue-800 dark:text-blue-200',
  }
  return map[status] || ''
}

/** Full status badge class (base + color). */
export const statusBadgeClass = (status: string): string => {
  const base = 'px-3 py-1 rounded-full text-xs font-medium'
  return `${base} ${getStatusBgColor(status)}`
}

/** Format an ISO datetime string for display. */
export const formatJobTime = (isoTime: string): string => {
  try {
    const dt = new Date(isoTime)
    return dt.toLocaleString()
  } catch {
    return isoTime
  }
}

/** Human-friendly relative time: "just now", "5m ago", "2 days ago", "1 week ago". */
export const humanizeRelativeTime = (isoTime: string): string => {
  try {
    const diff = Math.floor((Date.now() - new Date(isoTime).getTime()) / 1000)
    if (diff < 0) {
      const abs = Math.abs(diff)
      const h = Math.floor(abs / 3600)
      const m = Math.floor((abs % 3600) / 60)
      return h > 0 ? `in ${h}h ${m}m` : `in ${m}m`
    }
    if (diff < 60) return 'just now'
    if (diff < 3600) return `${Math.floor(diff / 60)}m ago`
    if (diff < 86400) return `${Math.floor(diff / 3600)}h ago`
    const days = Math.floor(diff / 86400)
    if (days < 7) return `${days} day${days > 1 ? 's' : ''} ago`
    const weeks = Math.floor(days / 7)
    return `${weeks} week${weeks > 1 ? 's' : ''} ago`
  } catch {
    return '-'
  }
}
