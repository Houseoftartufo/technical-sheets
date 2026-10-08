const test = require('node:test');
const assert = require('node:assert/strict');
const { normalize, score } = require('../_BUILD/search.js');

test('normalizes accents, German sharp s, punctuation, and case', () => {
  assert.equal(normalize('WEIß-Trüffel!'), 'weiss truffel');
});

test('finds a product despite a one-character typo', () => {
  assert.ok(score('carpacio', ['Carpaccio di Tartufo Estivo']) > 0);
});

test('matches partial words and query terms in any order across languages', () => {
  assert.ok(score('olio tartufo ner', [
    'Olio Extra Vergine al Tartufo Nero',
    'Olivenöl mit Sommertrüffel',
  ]) > 0);
});

test('does not match a product when a query term is absent', () => {
  assert.equal(score('olio salmone', ['Olio Extra Vergine al Tartufo Nero']), -1);
});

test('ranks an exact phrase ahead of a fuzzy match', () => {
  assert.ok(score('truffle', ['Truffle mayonnaise']) > score('truffle', ['Truffles aroma']));
});
