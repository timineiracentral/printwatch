import { downloadBlob, postFormData } from '../client'
import type { ImportEntity, ImportResult } from '../../types/api'

export function downloadImportTemplate(entity: ImportEntity): Promise<Blob> {
  return downloadBlob(`/import/templates/${entity}`)
}

export function importCsv(
  entity: ImportEntity,
  file: File,
  strict = false,
): Promise<ImportResult> {
  const formData = new FormData()
  formData.append('file', file)
  const qs = strict ? '?strict=true' : ''
  return postFormData<ImportResult>(`/import/${entity}${qs}`, formData)
}

export function triggerTemplateDownload(entity: ImportEntity, filename: string) {
  return downloadImportTemplate(entity).then((blob) => {
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = filename
    a.click()
    URL.revokeObjectURL(url)
  })
}
