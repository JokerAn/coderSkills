import { resolvePageSize } from './page-size.js';

export function previewRows(rows, pageSize) {
  return rows.slice(0, resolvePageSize(pageSize));
}
