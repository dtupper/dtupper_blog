const assert = require('node:assert/strict');
const { readFileSync } = require('node:fs');
const { join } = require('node:path');
const { test } = require('node:test');
const vm = require('node:vm');

const script = readFileSync(join(__dirname, '../generator/default_static/js/recency-badges.js'), 'utf8');

function renderBadge(dataset) {
    const classes = new Set();
    const badge = {
        dataset, hidden: true, textContent: '',
        classList: {
            add: (...names) => names.forEach(name => classes.add(name)),
            remove: (...names) => names.forEach(name => classes.delete(name)),
        },
    };
    class FixedDate extends Date {
        constructor(...args) {
            super(...(args.length ? args : [2024, 2, 15, 12]));
        }
    }
    vm.runInNewContext(script, {
        Date: FixedDate,
        document: { readyState: 'complete', querySelectorAll: () => [badge] },
    });
    return { ...badge, classes };
}

test('recent updates take priority over new-post badges', () => {
    const badge = renderBadge({ postedDate: '2024-03-15', updatedDate: '2024-03-14' });
    assert.equal(badge.hidden, false);
    assert.equal(badge.textContent, 'Recently Updated');
    assert.deepEqual([...badge.classes], ['badge-updated']);
});

test('configured cutoff includes its boundary and excludes older posts', () => {
    assert.equal(renderBadge({ postedDate: '2024-03-12', recentlyPostedDays: '3' }).hidden, false);
    assert.equal(renderBadge({ postedDate: '2024-03-11', recentlyPostedDays: '3' }).hidden, true);
});

test('future dates, invalid dates, and disabled badges do not claim recency', () => {
    assert.equal(renderBadge({ postedDate: '2025-03-15' }).hidden, true);
    assert.equal(renderBadge({ postedDate: '2024-02-31' }).hidden, true);
    assert.equal(renderBadge({ postedDate: '2024-03-15', recentlyPostedDays: '0' }).hidden, true);
});
