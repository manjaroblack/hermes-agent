// @ts-check
import assert from 'node:assert/strict';
import test from 'node:test';

function updateCompletionReached({ resultExists, shaMatches, markerExists }) {
  if (resultExists) return true;
  return Boolean(shaMatches && !markerExists);
}

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
