/* Shared fuzzy product search for browser runtime and Node tests. */
(function (root) {
  'use strict';

  function normalize(value) {
    return String(value || '')
      .toLocaleLowerCase()
      .replace(/ß/g, 'ss')
      .normalize('NFD')
      .replace(/[\u0300-\u036f]/g, '')
      .replace(/[^\p{L}\p{N}]+/gu, ' ')
      .trim()
      .replace(/\s+/g, ' ');
  }

  function distanceAtMostOne(a, b) {
    if (Math.abs(a.length - b.length) > 1) return false;
    var i = 0, j = 0, edits = 0;
    while (i < a.length && j < b.length) {
      if (a[i] === b[j]) { i++; j++; continue; }
      if (++edits > 1) return false;
      if (a.length > b.length) i++;
      else if (b.length > a.length) j++;
      else { i++; j++; }
    }
    if (i < a.length || j < b.length) edits++;
    return edits <= 1;
  }

  function termScore(term, fields) {
    var best = -1;
    fields.forEach(function (field) {
      var words = field.split(' ');
      words.forEach(function (word) {
        if (word === term) best = Math.max(best, 40);
        else if (word.indexOf(term) === 0 && term.length >= 3) best = Math.max(best, 30);
        else if (word.indexOf(term) >= 0 && term.length >= 4) best = Math.max(best, 22);
        else if (term.length >= 4 && distanceAtMostOne(term, word)) best = Math.max(best, 12);
      });
      if (field.indexOf(term) >= 0) best = Math.max(best, 18);
    });
    return best;
  }

  function score(query, values) {
    var normalizedQuery = normalize(query);
    if (!normalizedQuery) return 0;
    var fields = (Array.isArray(values) ? values : [values]).map(normalize).filter(Boolean);
    var terms = normalizedQuery.split(' '), total = 0;
    for (var i = 0; i < terms.length; i++) {
      var current = termScore(terms[i], fields);
      if (current < 0) return -1;
      total += current;
    }
    if (fields.some(function (field) { return field.indexOf(normalizedQuery) >= 0; })) total += 25;
    return total;
  }

  var api = { normalize: normalize, score: score };
  root.ProductSearch = api;
  if (typeof module !== 'undefined' && module.exports) module.exports = api;
})(typeof globalThis !== 'undefined' ? globalThis : this);
