export class DialogueSystem {
  constructor(data = {}) {
    this.data = data;
    this.active = null;
    this.index = 0;
    this.listeners = new Set();
  }

  onChange(listener) {
    this.listeners.add(listener);
    return () => this.listeners.delete(listener);
  }

  emit() {
    const state = this.getState();
    for (const listener of this.listeners) listener(state);
  }

  start(id) {
    const dialogue = this.data[id];
    if (!dialogue || !Array.isArray(dialogue.lines) || dialogue.lines.length === 0) return false;
    this.active = { id, speaker: dialogue.speaker ?? '', lines: dialogue.lines };
    this.index = 0;
    this.emit();
    return true;
  }

  advance() {
    if (!this.active) return false;
    if (this.index < this.active.lines.length - 1) {
      this.index += 1;
      this.emit();
      return true;
    }
    this.close();
    return true;
  }

  close() {
    this.active = null;
    this.index = 0;
    this.emit();
  }

  getState() {
    if (!this.active) return { active: false, speaker: '', text: '', index: 0, total: 0 };
    return {
      active: true,
      speaker: this.active.speaker,
      text: this.active.lines[this.index],
      index: this.index,
      total: this.active.lines.length
    };
  }
}
