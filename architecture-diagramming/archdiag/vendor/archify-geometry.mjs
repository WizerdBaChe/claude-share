// tools/archdiag/vendor/archify-geometry.mjs — geometry primitives vendored
// from tt-a1i/archify (MIT), renderers/shared/geometry.mjs, shallow clone
// @ 12106be58b34f94b108ab30f6ac0eb37c16a8f71 (2026-08-28).
//
// Upstream license: MIT — Copyright (c) 2026 tt-a1i (Archify),
// Copyright (c) 2025 Cocoon AI (original "architecture-diagram-generator").
// Full text: LICENSE at the upstream repository root. Vendored under the
// user ruling 2026-08-29 (selfbuild-scope-eval-2026-08-28.md §8 Q3); borrow
// ledger: outputs/skill-reviews/archify-integration-analysis-2026-08-28.md.
//
// Functions are verbatim cuts (upstream-internal helpers hoisted unchanged).
// Rects use upstream's {x, y, width, height} shape — adapt at the call
// boundary (tools/archdiag/route.mjs does), never edit shapes here.
// review-when: archify publishes a major version.

export function asArray(value) {
  return Array.isArray(value) ? value : [];
}

// A computed coordinate must be a finite number; NaN/undefined would silently
// write `<rect x="NaN">` into the output. Used by the validators as a backstop.
export function isFinitePoint(...coords) {
  return coords.every((c) => Number.isFinite(c));
}

export function rectsOverlap(a, b, gap = 0) {
  // Non-finite geometry means "unknown", not "overlapping". Every comparison
  // below is false for NaN, so without this guard the negation reports a
  // collision for every pair.
  if (!isFinitePoint(a.x, a.y, a.width, a.height, b.x, b.y, b.width, b.height)) {
    return false;
  }
  return !(
    a.x + a.width + gap <= b.x ||
    b.x + b.width + gap <= a.x ||
    a.y + a.height + gap <= b.y ||
    b.y + b.height + gap <= a.y
  );
}

export function segmentIntersectsRect(segment, rect, gap = 0) {
  const box = {
    x1: rect.x - gap,
    y1: rect.y - gap,
    x2: rect.x + rect.width + gap,
    y2: rect.y + rect.height + gap
  };
  const [a, b] = [segment.start, segment.end];
  if (pointInBox(a, box) || pointInBox(b, box)) return true;
  return (
    segmentsIntersect(a, b, [box.x1, box.y1], [box.x2, box.y1]) ||
    segmentsIntersect(a, b, [box.x2, box.y1], [box.x2, box.y2]) ||
    segmentsIntersect(a, b, [box.x2, box.y2], [box.x1, box.y2]) ||
    segmentsIntersect(a, b, [box.x1, box.y2], [box.x1, box.y1])
  );
}

const ENDPOINT_SIDE_RULES = {
  left: {
    axis: 'horizontal',
    sourceSign: -1,
    targetSign: 1,
    sourceDirection: 'leftward',
    targetDirection: 'rightward from the left',
  },
  right: {
    axis: 'horizontal',
    sourceSign: 1,
    targetSign: -1,
    sourceDirection: 'rightward',
    targetDirection: 'leftward from the right',
  },
  top: {
    axis: 'vertical',
    sourceSign: -1,
    targetSign: 1,
    sourceDirection: 'upward',
    targetDirection: 'downward from above',
  },
  bottom: {
    axis: 'vertical',
    sourceSign: 1,
    targetSign: -1,
    sourceDirection: 'downward',
    targetDirection: 'upward from below',
  },
};

function endpointSideIssue(points, endpoint, side) {
  const rule = ENDPOINT_SIDE_RULES[side];
  if (!rule) return null;
  const normalized = normalizeRoutePoints(points);
  if (normalized.length < 2) return null;
  const segmentIndex = endpoint === 'source' ? 0 : normalized.length - 2;
  const start = normalized[segmentIndex];
  const end = normalized[segmentIndex + 1];
  const dx = end[0] - start[0];
  const dy = end[1] - start[1];
  const along = rule.axis === 'horizontal' ? dx : dy;
  const across = rule.axis === 'horizontal' ? dy : dx;
  const expectedSign = endpoint === 'source' ? rule.sourceSign : rule.targetSign;
  if (Math.abs(across) <= 0.0001 && along * expectedSign > 0.0001) return null;
  return {
    endpoint,
    side,
    segmentIndex,
    start,
    end,
    expectedAxis: rule.axis,
    expectedDirection: endpoint === 'source' ? rule.sourceDirection : rule.targetDirection,
  };
}

// A side is a direction contract, not just a point on a box border. This pure
// predicate lets automatic routers prefer a dogleg whose first and final
// segments leave/enter the chosen sides perpendicularly.
export function routeHonorsEndpointSides(points, fromSide, toSide) {
  return !endpointSideIssue(points, 'source', fromSide)
    && !endpointSideIssue(points, 'target', toSide);
}

export function normalizeRoutePoints(points) {
  const finite = asArray(points).filter((point) => Array.isArray(point) && point.length === 2 && isFinitePoint(...point));
  const deduped = [];
  for (const point of finite) {
    const previous = deduped.at(-1);
    if (!previous || Math.abs(point[0] - previous[0]) > 0.0001 || Math.abs(point[1] - previous[1]) > 0.0001) deduped.push(point);
  }
  const normalized = [];
  for (const point of deduped) {
    while (normalized.length >= 2 && collinearForward(normalized.at(-2), normalized.at(-1), point)) normalized.pop();
    normalized.push(point);
  }
  return normalized;
}

function collinearForward(a, b, c) {
  if (Math.abs(crossProduct(a, b, c)) > 0.0001) return false;
  return (b[0] - a[0]) * (c[0] - b[0]) + (b[1] - a[1]) * (c[1] - b[1]) >= -0.0001;
}

function crossProduct(a, b, c) {
  return (b[0] - a[0]) * (c[1] - a[1]) - (b[1] - a[1]) * (c[0] - a[0]);
}

function pointInBox(point, box) {
  return point[0] >= box.x1 && point[0] <= box.x2 && point[1] >= box.y1 && point[1] <= box.y2;
}

function segmentsIntersect(a, b, c, d) {
  const o1 = orientation(a, b, c);
  const o2 = orientation(a, b, d);
  const o3 = orientation(c, d, a);
  const o4 = orientation(c, d, b);

  if (o1 === 0 && onSegment(a, c, b)) return true;
  if (o2 === 0 && onSegment(a, d, b)) return true;
  if (o3 === 0 && onSegment(c, a, d)) return true;
  if (o4 === 0 && onSegment(c, b, d)) return true;

  return o1 !== o2 && o3 !== o4;
}

function orientation(a, b, c) {
  const value = (b[1] - a[1]) * (c[0] - b[0]) - (b[0] - a[0]) * (c[1] - b[1]);
  if (Math.abs(value) < 0.0001) return 0;
  return value > 0 ? 1 : 2;
}

function onSegment(a, b, c) {
  return (
    b[0] <= Math.max(a[0], c[0]) &&
    b[0] >= Math.min(a[0], c[0]) &&
    b[1] <= Math.max(a[1], c[1]) &&
    b[1] >= Math.min(a[1], c[1])
  );
}
