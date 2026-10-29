export class DomainError extends Error {
  constructor(status, code, message) {
    super(message);
    this.status = status;
    this.code = code;
  }
}

const order = (a, b) => a < b ? -1 : a > b ? 1 : 0;
const copy = (value) => structuredClone(value);

export function createStore(seed) {
  const studios = copy(seed.studios);
  const assets = new Map(seed.assets.map(asset => [asset.id, copy(asset)]));
  let datasetRevision = seed.datasetRevision;

  function requireStudio(studio) {
    if (!studio || !studios.some(item => item.id === studio)) {
      throw new DomainError(400, 'INVALID_STUDIO', 'Choose a known studio.');
    }
  }

  function findAsset(id, studio) {
    requireStudio(studio);
    const asset = assets.get(id);
    if (!asset || asset.studioId !== studio) {
      throw new DomainError(404, 'ASSET_NOT_FOUND', 'Asset not found in this studio.');
    }
    return asset;
  }

  function listAssets({ studio, status = '', q = '', limit = 50 }) {
    requireStudio(studio);
    if (status && !['ready', 'processing', 'archived'].includes(status)) {
      throw new DomainError(400, 'INVALID_STATUS', 'Unknown status.');
    }
    if (!Number.isSafeInteger(limit) || limit < 1 || limit > 100) {
      throw new DomainError(400, 'INVALID_LIMIT', 'Limit must be from 1 to 100.');
    }
    const query = String(q).trim().toLowerCase();
    const all = [...assets.values()].filter(asset =>
      asset.studioId === studio && (!status || asset.status === status) &&
      (!query || [asset.id, asset.title, asset.series].some(value => value.toLowerCase().includes(query)))
    ).sort((a, b) => order(a.title, b.title) || order(a.id, b.id));
    return {
      studio,
      datasetRevision,
      total: all.length,
      assets: all.slice(0, limit).map(asset => ({
        id: asset.id, studioId: asset.studioId, title: asset.title, series: asset.series,
        status: asset.status, durationMs: asset.durationMs,
        supportedLocales: [...asset.supportedLocales], revision: asset.revision
      }))
    };
  }

  function getAsset(id, studio) {
    return { asset: copy(findAsset(id, studio)), datasetRevision };
  }

  function editNote(id, studio, note, expectedRevision) {
    const asset = findAsset(id, studio);
    if (typeof note !== 'string' || !note.trim() || note.trim().length > 500) {
      throw new DomainError(400, 'INVALID_NOTE', 'Note must contain 1–500 non-whitespace characters.');
    }
    if (!Number.isSafeInteger(expectedRevision) || expectedRevision < 0) {
      throw new DomainError(400, 'INVALID_REVISION', 'Expected revision must be a nonnegative integer.');
    }
    if (asset.revision !== expectedRevision) {
      throw new DomainError(409, 'STALE_REVISION', 'Asset has changed. Refresh before editing.');
    }
    const next = note.trim();
    if (next !== asset.note) {
      asset.note = next;
      asset.revision += 1;
      datasetRevision += 1;
    }
    return { asset: copy(asset), datasetRevision };
  }

  return {
    listStudios: () => ({ studios: copy(studios), datasetRevision }),
    listAssets, getAsset, editNote,
    snapshot: () => ({ studios: copy(studios), assets: [...assets.values()].map(copy), datasetRevision })
  };
}
