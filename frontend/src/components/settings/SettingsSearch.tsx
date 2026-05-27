import { Input } from '../ui/Input'

export interface SettingsSearchProps {
  value: string
  onChange: (value: string) => void
  placeholder?: string
}

export function SettingsSearch({
  value,
  onChange,
  placeholder = 'Buscar…',
}: SettingsSearchProps) {
  return (
    <div className="w-full max-w-[240px]">
      <Input
        type="search"
        value={value}
        onChange={(e) => onChange(e.target.value)}
        placeholder={placeholder}
        aria-label="Buscar na tabela"
      />
    </div>
  )
}
