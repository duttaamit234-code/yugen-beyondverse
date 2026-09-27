export const ASSET_MANIFEST = Object.freeze({
  environment: [],
  characters: [],
  audio: [],
  ui: [],
});

export function getAssetCategory(category) {
  return ASSET_MANIFEST[category] ?? [];
}
