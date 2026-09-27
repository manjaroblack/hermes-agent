// @ts-check
import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import test from 'node:test';

const source = fs.readFileSync(new URL('./launch-from-spec.mjs', import.meta.url), 'utf8');
const start = source.indexOf('export function updateCompletionReached');
const end = source.indexOf('/** @param {string} msg */');
if (start < 0 || end < start) {
  throw new Error('update completion helpers are missing from launch-from-spec.mjs');
}
const loaded = new Function(
  'path',
  `${source.slice(start, end).replace(/^export /gm, '')}\nreturn { updateCompletionReached, updateMarkerPath };`,
)(path);
const { updateCompletionReached, updateMarkerPath } = loaded;

test('result file completes the update even if the marker is still present', () => {
  assert.equal(
    updateCompletionReached({ resultExists: true, shaMatches: false, markerExists: true }),
    true,
  );
});

test('a SHA match is not completion while the Windows hand-off still holds the marker', () => {
  assert.equal(
    updateCompletionReached({ resultExists: false, shaMatches: true, markerExists: true }),
    false,
  );
});

test('a SHA match completes the update once the marker is gone', () => {
  assert.equal(
    updateCompletionReached({ resultExists: false, shaMatches: true, markerExists: false }),
    true,
  );
});

test('neither signal means the update is still running', () => {
  assert.equal(
    updateCompletionReached({ resultExists: false, shaMatches: false, markerExists: false }),
    false,
  );
});

test('the marker sits beside the result file', () => {
  const result = path.join('hermes-home', '.hermes-update-result.json');
  assert.equal(
    updateMarkerPath(result),
    path.join('hermes-home', '.hermes-update-in-progress'),
  );
  assert.equal(updateMarkerPath(''), '');
});
