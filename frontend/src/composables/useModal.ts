import { ref, watch, onUnmounted, type Ref } from 'vue'

const FOCUSABLE = 'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'

export function useModal(visible: Ref<boolean>, onClose?: () => void) {
  const panelRef = ref<HTMLElement | null>(null)
  let previousFocus: HTMLElement | null = null

  const trapFocus = (e: KeyboardEvent) => {
    if (!visible.value || e.key !== 'Tab' || !panelRef.value) return

    const focusable = Array.from(
      panelRef.value.querySelectorAll<HTMLElement>(FOCUSABLE)
    ).filter(el => !el.hasAttribute('disabled'))

    if (focusable.length === 0) return

    const first = focusable[0]
    const last = focusable[focusable.length - 1]

    if (e.shiftKey && document.activeElement === first) {
      e.preventDefault()
      last.focus()
    } else if (!e.shiftKey && document.activeElement === last) {
      e.preventDefault()
      first.focus()
    }
  }

  const onKeydown = (e: KeyboardEvent) => {
    if (!visible.value) return
    if (e.key === 'Escape') {
      e.preventDefault()
      onClose?.()
    }
    trapFocus(e)
  }

  watch(visible, (open) => {
    if (open) {
      previousFocus = document.activeElement as HTMLElement
      document.addEventListener('keydown', onKeydown)
      requestAnimationFrame(() => {
        const first = panelRef.value?.querySelector<HTMLElement>(FOCUSABLE)
        first?.focus()
      })
    } else {
      document.removeEventListener('keydown', onKeydown)
      previousFocus?.focus()
      previousFocus = null
    }
  })

  onUnmounted(() => {
    document.removeEventListener('keydown', onKeydown)
  })

  return { panelRef }
}
