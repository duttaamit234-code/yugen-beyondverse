const THEMES = {
  village: { notes: [110, 164.81, 220], interval: 4200, volume: 0.045, wave: 'sine' },
  forest: { notes: [73.42, 110, 146.83], interval: 3600, volume: 0.035, wave: 'triangle' },
  shrine: { notes: [65.41, 98, 130.81], interval: 5200, volume: 0.04, wave: 'sine' },
  ruins: { notes: [82.41, 123.47, 164.81], interval: 3000, volume: 0.038, wave: 'triangle' }
};

export class AmbientAudio {
  constructor() {
    this.ctx = null;
    this.master = null;
    this.timer = null;
    this.theme = null;
    this.step = 0;
    this.unlockBound = () => this.unlock();
  }

  attach() {
    window.addEventListener('pointerdown', this.unlockBound, { passive: true });
    window.addEventListener('keydown', this.unlockBound, { passive: true });
  }

  unlock() {
    if (!this.ctx) {
      const AudioContext = window.AudioContext || window.webkitAudioContext;
      if (!AudioContext) return;
      this.ctx = new AudioContext();
      this.master = this.ctx.createGain();
      this.master.gain.value = 0.28;
      this.master.connect(this.ctx.destination);
    }
    if (this.ctx.state === 'suspended') this.ctx.resume();
    if (this.theme) this.playPulse();
  }

  setTheme(theme) {
    if (!THEMES[theme]) return;
    this.theme = theme;
    this.step = 0;
    if (this.timer) clearInterval(this.timer);
    const data = THEMES[theme];
    this.timer = setInterval(() => this.playPulse(), data.interval);
    this.playPulse();
  }

  playPulse() {
    if (!this.ctx || this.ctx.state !== 'running' || !this.theme) return;
    const data = THEMES[this.theme];
    const now = this.ctx.currentTime;
    const root = data.notes[this.step % data.notes.length];
    this.step += 1;

    const osc = this.ctx.createOscillator();
    const gain = this.ctx.createGain();
    osc.type = data.wave;
    osc.frequency.setValueAtTime(root, now);
    gain.gain.setValueAtTime(0.0001, now);
    gain.gain.exponentialRampToValueAtTime(data.volume, now + 0.55);
    gain.gain.exponentialRampToValueAtTime(0.0001, now + 3.2);
    osc.connect(gain).connect(this.master);
    osc.start(now);
    osc.stop(now + 3.3);

    const fifth = this.ctx.createOscillator();
    const fifthGain = this.ctx.createGain();
    fifth.type = 'sine';
    fifth.frequency.value = root * 1.5;
    fifthGain.gain.setValueAtTime(0.0001, now);
    fifthGain.gain.exponentialRampToValueAtTime(data.volume * 0.28, now + 0.8);
    fifthGain.gain.exponentialRampToValueAtTime(0.0001, now + 2.8);
    fifth.connect(fifthGain).connect(this.master);
    fifth.start(now);
    fifth.stop(now + 2.9);
  }

  chime(kind = 'interact') {
    if (!this.ctx || this.ctx.state !== 'running') return;
    const now = this.ctx.currentTime;
    const osc = this.ctx.createOscillator();
    const gain = this.ctx.createGain();
    osc.type = 'sine';
    osc.frequency.value = kind === 'dialogue' ? 520 : 680;
    gain.gain.setValueAtTime(0.0001, now);
    gain.gain.exponentialRampToValueAtTime(kind === 'dialogue' ? 0.018 : 0.035, now + 0.015);
    gain.gain.exponentialRampToValueAtTime(0.0001, now + 0.22);
    osc.connect(gain).connect(this.master);
    osc.start(now);
    osc.stop(now + 0.24);
  }

  destroy() {
    if (this.timer) clearInterval(this.timer);
    window.removeEventListener('pointerdown', this.unlockBound);
    window.removeEventListener('keydown', this.unlockBound);
    if (this.ctx) this.ctx.close();
  }
}

export const ambientAudio = new AmbientAudio();
ambientAudio.attach();
