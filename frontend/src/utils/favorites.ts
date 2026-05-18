const STORAGE_KEY = 'mlctl-channel-favorites'

export function loadFavoriteArns(): string[] {
  try {
    const raw = localStorage.getItem(STORAGE_KEY)
    if (!raw) return []
    const parsed = JSON.parse(raw)
    return Array.isArray(parsed) ? parsed.filter((x): x is string => typeof x === 'string') : []
  } catch {
    return []
  }
}

export function saveFavoriteArns(arns: string[]) {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(arns))
}

export function toggleFavoriteArn(arn: string): string[] {
  const current = loadFavoriteArns()
  const next = current.includes(arn)
    ? current.filter(a => a !== arn)
    : [...current, arn]
  saveFavoriteArns(next)
  return next
}

export function sortChannelsByFavorites<T extends { arn: string }>(channels: T[]): T[] {
  const favorites = new Set(loadFavoriteArns())
  return [...channels].sort((a, b) => {
    const af = favorites.has(a.arn) ? 0 : 1
    const bf = favorites.has(b.arn) ? 0 : 1
    if (af !== bf) return af - bf
    return a.arn.localeCompare(b.arn)
  })
}
