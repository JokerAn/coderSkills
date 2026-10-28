# Shared page-size fixture

This is a dependency-free front-end view-model fixture. `src/list-view.js` selects rows for the page; `src/export-preview.js` selects rows for the export preview. Both accept the same page-size setting.

The input contract is a non-negative integer, null, or undefined. Zero means display no rows. Null and undefined use the default size of 10. Other non-negative integers select that many rows, bounded by the available rows. Inputs outside this contract are out of scope.

Run `npm test` with Node.js 18 or later. No installation, network, browser, or build step is required.
