import { useCallback, useSyncExternalStore } from 'react'

const STORAGE_KEY = 'printwatch.showCostColumn'
const CHANGE_EVENT = 'printwatch:show-cost-column'

function readStored(): boolean {
  try {
    return localStorage.getItem(STORAGE_KEY) === 'true'
  } catch {
    return false
  }
}

function subscribe(onStoreChange: () => void): () => void {
  const handler = () => onStoreChange()
  const onStorage = (e: StorageEvent) => {
    if (e.key === STORAGE_KEY || e.key === null) onStoreChange()
  }
  window.addEventListener('storage', onStorage)
  window.addEventListener(CHANGE_EVENT, handler)
  return () => {
    window.removeEventListener('storage', onStorage)
    window.removeEventListener(CHANGE_EVENT, handler)
  }
}

export function useShowCostColumn() {
  const show = useSyncExternalStore(subscribe, readStored, () => false)

  const setShow = useCallback((value: boolean) => {
    try {
      localStorage.setItem(STORAGE_KEY, value ? 'true' : 'false')
      window.dispatchEvent(new Event(CHANGE_EVENT))
    } catch {
      /* ignore quota / private mode */
    }
  }, [])

  return { showCostColumn: show, setShowCostColumn: setShow }
}
