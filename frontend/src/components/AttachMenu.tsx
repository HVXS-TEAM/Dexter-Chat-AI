import { useEffect, useRef } from 'react'

interface AttachMenuProps {
  onFilesSelected: (files: File[]) => void
  onClose: () => void
}

interface AttachOptionProps {
  icon: string
  title: string
  subtitle: string
  accept: string
  onFilesSelected: (files: File[]) => void
}

function AttachOption({ icon, title, subtitle, accept, onFilesSelected }: AttachOptionProps) {
  const inputRef = useRef<HTMLInputElement | null>(null)

  function handleChange() {
    const files = inputRef.current?.files
    if (files) {
      onFilesSelected(Array.from(files))
    }
    if (inputRef.current) {
      inputRef.current.value = ''
    }
  }

  return (
    <button
      className="flex w-full items-center gap-3 rounded-[8px] px-3 py-2 text-left hover:bg-[var(--surface-container)] focus-visible:outline focus-visible:outline-2 focus-visible:outline-[var(--primary)]"
      type="button"
      role="menuitem"
      onClick={() => inputRef.current?.click()}
    >
      <span className="material-symbols-outlined text-[var(--primary)]" aria-hidden="true">{icon}</span>
      <span className="min-w-0">
        <span className="block text-sm font-semibold text-[var(--text-primary)]">{title}</span>
        <span className="block truncate text-xs text-[var(--text-secondary)]">{subtitle}</span>
      </span>
      <input ref={inputRef} className="hidden" type="file" multiple accept={accept} onChange={handleChange} />
    </button>
  )
}

export default function AttachMenu({ onFilesSelected, onClose }: AttachMenuProps) {
  const menuRef = useRef<HTMLDivElement | null>(null)

  useEffect(() => {
    function handlePointerDown(event: PointerEvent) {
      if (menuRef.current && !menuRef.current.contains(event.target as Node)) {
        onClose()
      }
    }

    function handleKeyDown(event: KeyboardEvent) {
      if (event.key === 'Escape') {
        onClose()
      }
    }

    document.addEventListener('pointerdown', handlePointerDown)
    document.addEventListener('keydown', handleKeyDown)
    return () => {
      document.removeEventListener('pointerdown', handlePointerDown)
      document.removeEventListener('keydown', handleKeyDown)
    }
  }, [onClose])

  return (
    <div ref={menuRef} className="absolute bottom-14 left-0 z-30 w-72 rounded-[12px] border border-[var(--border-default)] bg-[var(--surface)] p-2 shadow-lg" role="menu">
      <AttachOption
        icon="description"
        title="Document de cours"
        subtitle="PDF, Word, PowerPoint, TXT, Markdown"
        accept=".pdf,.docx,.pptx,.txt,.md"
        onFilesSelected={onFilesSelected}
      />
      <AttachOption
        icon="image"
        title="Image"
        subtitle="PNG, JPG — OCR intégré"
        accept=".png,.jpg,.jpeg"
        onFilesSelected={onFilesSelected}
      />
    </div>
  )
}