const SAVE_KEY = 'yugen-beyondverse-save-v1';

export class SaveSystem {
  constructor(storage = globalThis.localStorage) {
    this.storage = storage;
  }
  save(state) {
    try {
      const payload = { version: 1, savedAt: Date.now(), state };
      this.storage.setItem(SAVE_KEY, JSON.stringify(payload));
      return true;
    } catch (error) {
      console.error('Save failed:', error);
      return false;
    }
  }
  load() {
    try {
      const raw = this.storage.getItem(SAVE_KEY);
      if (!raw) return null;
      const payload = JSON.parse(raw);
      if (payload?.version !== 1 || !payload.state) return null;
      return payload.state;
    } catch (error) {
      console.error('Load failed:', error);
      return null;
    }
  }
  clear() {
    try { this.storage.removeItem(SAVE_KEY); return true; }
    catch (error) { console.error('Clear save failed:', error); return false; }
  }
}
