import { resolvePageSize } from './page-size.js';

export function visibleRows(rows, pageSize) {
  return rows.slice(0, resolvePageSize(pageSize));
}
