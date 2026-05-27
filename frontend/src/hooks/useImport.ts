import { useMutation } from '@tanstack/react-query'
import { importCsv } from '../api/settings/import'
import type { ImportEntity } from '../types/api'

export function useImportCsv() {
  return useMutation({
    mutationFn: ({
      entity,
      file,
      strict,
    }: {
      entity: ImportEntity
      file: File
      strict?: boolean
    }) => importCsv(entity, file, strict),
  })
}
