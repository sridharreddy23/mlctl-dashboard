/** Guess IANA timezone for schedule defaults (Python 3.8 / browser). */
export function detectTimezone(): string {
  try {
    let tz = Intl.DateTimeFormat().resolvedOptions().timeZone || 'UTC'
    if (tz === 'Asia/Calcutta') tz = 'Asia/Kolkata'
    return tz
  } catch {
    return 'UTC'
  }
}

export const COMMON_TIMEZONES = [
  'UTC',
  'Asia/Kolkata',
  'America/New_York',
  'America/Los_Angeles',
  'Europe/London',
  'Asia/Tokyo',
] as const

export function timezoneOptions(detected: string): string[] {
  const set = new Set<string>([...COMMON_TIMEZONES])
  if (detected) set.add(detected)
  return Array.from(set)
}
