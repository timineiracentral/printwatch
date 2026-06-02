import { useState } from 'react'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { createMeterReading } from '../../api/manager'
import type { MeterReadingCreate } from '../../types/api'
import { Button } from '../ui/Button'

export interface MeterReadingDialogProps {
  printerId: number
  printerName: string
  open: boolean
  onClose: () => void
}

export function MeterReadingDialog({
  printerId,
  printerName,
  open,
  onClose,
}: MeterReadingDialogProps) {
  const queryClient = useQueryClient()
  const [counterTotal, setCounterTotal] = useState('')
  const [counterMono, setCounterMono] = useState('')
  const [counterColor, setCounterColor] = useState('')
  const [error, setError] = useState<string | null>(null)

  const mutation = useMutation({
    mutationFn: (payload: MeterReadingCreate) =>
      createMeterReading(printerId, payload),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ['manager'] })
      onClose()
      setCounterTotal('')
      setCounterMono('')
      setCounterColor('')
      setError(null)
    },
    onError: (err: Error) => {
      setError(err.message)
    },
  })

  if (!open) {
    return null
  }

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    const total = Number(counterTotal)
    if (Number.isNaN(total) || total < 0) {
      setError('Informe um contador total válido')
      return
    }
    const payload: MeterReadingCreate = {
      timestamp: new Date().toISOString(),
      counter_total: total,
      counter_mono: counterMono ? Number(counterMono) : null,
      counter_color: counterColor ? Number(counterColor) : null,
      source: 'manual',
    }
    mutation.mutate(payload)
  }

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/30 p-4"
      role="dialog"
      aria-modal="true"
      aria-labelledby="meter-dialog-title"
    >
      <form
        onSubmit={handleSubmit}
        className="w-full max-w-md rounded-xl border border-[var(--border)] bg-[var(--bg-surface)] p-6 shadow-lg"
      >
        <h2 id="meter-dialog-title" className="text-lg font-semibold">
          Leitura de contador — {printerName}
        </h2>
        <div className="mt-4 flex flex-col gap-3">
          <label className="text-sm">
            Contador total
            <input
              type="number"
              min={0}
              required
              className="mt-1 w-full rounded-lg border border-[var(--border)] px-2 py-1.5"
              value={counterTotal}
              onChange={(e) => setCounterTotal(e.target.value)}
            />
          </label>
          <label className="text-sm">
            Mono (opcional)
            <input
              type="number"
              min={0}
              className="mt-1 w-full rounded-lg border border-[var(--border)] px-2 py-1.5"
              value={counterMono}
              onChange={(e) => setCounterMono(e.target.value)}
            />
          </label>
          <label className="text-sm">
            Color (opcional)
            <input
              type="number"
              min={0}
              className="mt-1 w-full rounded-lg border border-[var(--border)] px-2 py-1.5"
              value={counterColor}
              onChange={(e) => setCounterColor(e.target.value)}
            />
          </label>
        </div>
        {error ? (
          <p className="mt-3 text-sm text-red-700" role="alert">
            {error}
          </p>
        ) : null}
        <div className="mt-6 flex justify-end gap-2">
          <Button type="button" variant="secondary" onClick={onClose}>
            Cancelar
          </Button>
          <Button type="submit" disabled={mutation.isPending}>
            Salvar
          </Button>
        </div>
      </form>
    </div>
  )
}
