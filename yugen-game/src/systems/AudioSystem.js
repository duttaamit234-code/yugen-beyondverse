// Lightweight procedural soundtrack. No external audio files are required.
// Four looping themes are generated with Web Audio so the web build stays small.
export default class AudioSystem {
  constructor(scene) {
    this.scene = scene;
    this.ctx = null;
    this.master = null;
    this.timer = null;
    this.theme = 1;
    this.step = 0;
    this.started = false;
    this.boundStart = () => this.start();

    scene.input.once('pointerdown', this.boundStart);
    scene.input.keyboard?.once('keydown', this.boundStart);
  }

  start() {
    if (this.started) {
      if (this.ctx?.state === 'suspended') this.ctx.resume();
      return;
    }

    const Ctx = window.AudioContext || window.webkitAudioContext;
    if (!Ctx) return;

    this.ctx = new Ctx();
    this.master = this.ctx.createGain();
    this.master.gain.value = 0.075;
    this.master.connect(this.ctx.destination);
    this.started = true;
    this.step = 0;
    this.scheduleLoop();
  }

  setTheme(theme) {
    this.theme = Math.max(1, Math.min(4, theme));
    this.step = 0;
    if (!this.started) return;
  }

  scheduleLoop() {
    if (this.timer) clearInterval(this.timer);
    this.playBeat();
    this.timer = setInterval(() => this.playBeat(), 1800);
  }

  note(freq, duration = 1.25, type = 'sine', volume = 0.18, when = 0) {
    if (!this.ctx || !this.master) return;
    const now = this.ctx.currentTime + when;
    const osc = this.ctx.createOscillator();
    const gain = this.ctx.createGain();
    osc.type = type;
    osc.frequency.setValueAtTime(freq, now);
    gain.gain.setValueAtTime(0.0001, now);
    gain.gain.exponentialRampToValueAtTime(volume, now + 0.08);
    gain.gain.exponentialRampToValueAtTime(0.0001, now + duration);
    osc.connect(gain).connect(this.master);
    osc.start(now);
    osc.stop(now + duration + 0.03);
  }

  playBeat() {
    if (!this.started) return;
    const themes = {
      // Village: warm but slightly unresolved.
      1: { bass: [110, 123.47, 98, 110], lead: [220, 246.94, 293.66, 246.94] },
      // Forest: lower, sparse, with a repeating three-note question.
      2: { bass: [82.41, 92.5, 82.41, 73.42], lead: [164.81, 185, 155.56, 146.83] },
      // Mirror: suspended/minor, deliberately uncanny.
      3: { bass: [73.42, 87.31, 69.3, 82.41], lead: [220, 207.65, 246.94, 184.99] },
      // Ruins: deeper and more spacious, with a slow resolving phrase.
      4: { bass: [55, 65.41, 73.42, 49], lead: [110, 130.81, 146.83, 98] }
    };
    const t = themes[this.theme];
    const i = this.step % 4;
    this.note(t.bass[i], 1.65, 'sine', 0.22);
    this.note(t.lead[i], 1.05, this.theme >= 3 ? 'triangle' : 'sine', 0.105, 0.12);
    if (this.theme === 1 && i === 0) this.note(329.63, 0.8, 'sine', 0.045, 0.45);
    if (this.theme === 2 && i === 2) this.note(123.47, 1.1, 'triangle', 0.05, 0.35);
    if (this.theme === 3 && i === 1) this.note(311.13, 0.75, 'triangle', 0.04, 0.5);
    if (this.theme === 4 && i === 3) this.note(196, 1.2, 'sine', 0.04, 0.4);
    this.step++;
  }

  sfx(kind = 'interact') {
    if (!this.started) this.start();
    const sounds = {
      interact: [660, 0.09],
      dialogue: [440, 0.07],
      memory: [330, 0.25],
      clue: [523.25, 0.32],
      transition: [220, 0.65]
    };
    const [freq, duration] = sounds[kind] || sounds.interact;
    this.note(freq, duration, kind === 'transition' ? 'sine' : 'triangle', 0.13);
    if (kind === 'clue') this.note(freq * 1.5, duration * 0.75, 'sine', 0.06, 0.08);
  }

  destroy() {
    if (this.timer) clearInterval(this.timer);
    this.timer = null;
  }
}
