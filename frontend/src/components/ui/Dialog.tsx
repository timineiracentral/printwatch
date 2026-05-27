import {
  Dialog as HDialog,
  DialogPanel,
  DialogTitle,
} from '@headlessui/react'
import type { ReactNode } from 'react'
import { X } from 'lucide-react'

export interface DialogProps {
  open: boolean
  onClose: () => void
  title: string
  children: ReactNode
  footer?: ReactNode
}

export function Dialog({ open, onClose, title, children, footer }: DialogProps) {
  return (
    <HDialog open={open} onClose={onClose} className="relative z-50">
      <div className="fixed inset-0 bg-black/20" aria-hidden="true" />
      <div className="fixed inset-0 flex items-center justify-center p-4">
        <DialogPanel
          className={[
            'max-h-[90vh] w-full max-w-lg overflow-y-auto rounded-xl border border-[var(--border-subtle)]',
            'bg-[var(--bg-surface)] p-6 shadow-[0_8px_32px_rgba(0,0,0,0.12)]',
          ].join(' ')}
        >
          <div className="mb-4 flex items-start justify-between gap-4">
            <DialogTitle
              id="dialog-title"
              className="text-[17px] font-semibold text-[var(--text-primary)]"
            >
              {title}
            </DialogTitle>
            <button
              type="button"
              className="rounded p-1 text-[var(--text-tertiary)] hover:bg-[var(--row-hover)] hover:text-[var(--text-primary)]"
              aria-label="Fechar"
              onClick={onClose}
            >
              <X className="size-5" aria-hidden />
            </button>
          </div>
          <div className="flex flex-col gap-4">{children}</div>
          {footer ? (
            <div className="mt-6 flex justify-end gap-2 border-t border-[var(--border-subtle)] pt-4">
              {footer}
            </div>
          ) : null}
        </DialogPanel>
      </div>
    </HDialog>
  )
}
