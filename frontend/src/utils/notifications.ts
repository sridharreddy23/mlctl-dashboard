/**
 * Browser Notification API helpers.
 */

let permissionGranted = false

export async function requestNotificationPermission(): Promise<boolean> {
  if (!('Notification' in window)) return false
  if (Notification.permission === 'granted') {
    permissionGranted = true
    return true
  }
  if (Notification.permission === 'denied') return false
  const result = await Notification.requestPermission()
  permissionGranted = result === 'granted'
  return permissionGranted
}

export function notify(title: string, body: string): void {
  if (!permissionGranted || !('Notification' in window)) return
  try {
    new Notification(title, { body, tag: `mlctl-${Date.now()}` })
  } catch { /* silent */ }
}

export function detectJobChanges(
  oldStatuses: Record<string, string>,
  jobs: Array<{ id: string; name: string; status: string }>
): Record<string, string> {
  const newStatuses: Record<string, string> = {}
  for (const job of jobs) {
    newStatuses[job.id] = job.status
    const prev = oldStatuses[job.id]
    if (!prev) continue
    if (prev !== job.status) {
      if (job.status === 'done') notify('✅ Job Completed', `${job.name} finished successfully`)
      else if (job.status === 'failed') notify('❌ Job Failed', `${job.name} has failed`)
    }
  }
  return newStatuses
}
