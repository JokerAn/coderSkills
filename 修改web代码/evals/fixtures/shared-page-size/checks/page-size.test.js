import test from 'node:test';
import assert from 'node:assert/strict';
import { visibleRows } from '../src/list-view.js';
import { previewRows } from '../src/export-preview.js';

const rows = Array.from({ length: 12 }, (_, index) => ({ id: index + 1 }));

for (const [name, select] of [['list', visibleRows], ['export preview', previewRows]]) {
  test(`${name}: zero selects no rows`, () => {
    assert.deepEqual(select(rows, 0), []);
  });

  test(`${name}: null and undefined use ten rows`, () => {
    for (const value of [null, undefined]) {
      assert.deepEqual(select(rows, value), rows.slice(0, 10));
    }
  });

  test(`${name}: explicit sizes preserve order and available rows`, () => {
    assert.deepEqual(select(rows, 3), rows.slice(0, 3));
    assert.deepEqual(select(rows, 20), rows);
    assert.deepEqual(rows.map(row => row.id), Array.from({ length: 12 }, (_, i) => i + 1));
  });
}
