const KEY = 'yugen-beyondverse-save-v1';

export function defaultSave() {
  return {
    chapter: 1,
    stage: 'meetOldWoman',
    flags: {
      introComplete: false,
      oldWomanMet: false,
      stoneSeen: false,
      photographFound: false,
      villageShifted: false,
      oldWomanSecondMet: false,
      chapter2Started: false,
      forestEchoSeen: false,
      shrineFound: false,
      mirrorSeen: false,
      mirrorMemorySeen: false,
      ruinsFound: false,
      otherYouMet: false,
      chapter4Complete: false
    },
    player: { x: 1595, y: 1075 }
  };
}

export function loadSave() {
  try {
    const raw = localStorage.getItem(KEY);
    if (!raw) return defaultSave();
    const parsed = JSON.parse(raw);
    return {
      ...defaultSave(),
      ...parsed,
      flags: { ...defaultSave().flags, ...(parsed.flags || {}) },
      player: { ...defaultSave().player, ...(parsed.player || {}) }
    };
  } catch {
    return defaultSave();
  }
}

export function saveGame(state) {
  try {
    // Chapter 1 hands control to the dedicated chapter 2-4 scene.
    if (state.stage === 'complete' && !state.flags.chapter4Complete) {
      state.chapter = 2;
      state.stage = 'chapter2Gate';
      state.flags.chapter2Started = true;
      window.dispatchEvent(new CustomEvent('yugen-start-chapter2'));
    }
    localStorage.setItem(KEY, JSON.stringify(state));
    return true;
  } catch {
    return false;
  }
}

export function clearSave() {
  try { localStorage.removeItem(KEY); } catch { /* Ignore storage failures. */ }
}
