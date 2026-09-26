// Four original procedural themes. They loop continuously and require no external
// copyrighted music assets, keeping the web build small and easy to package later.
const THEMES = {
  village: {
    notes: [110, 123.47, 146.83, 164.81, 146.83, 123.47, 110, 98],
    interval: 1450,
    volume: 0.032,
    wave: 'sine',
    accent: 1.5
  },
  forest: {
    notes: [73.42, 82.41, 98, 82.41, 73.42, 110, 98, 82.41],
    interval: 1300,
    volume: 0.028,
    wave: 'triangle',
    accent: 1.5
  },
  shrine: {
    notes: [65.41, 77.78, 98, 92.5, 73.42, 110, 82.41, 69.3],
    interval: 1750,
    volume: 0.03,
    wave: 'sine',
    accent: 1.414
  },
  ruins: {
    notes: [55, 65.41, 73.42, 82.41, 73.42, 65.41, 49, 61.74],
    interval: 1550,
    volume: 0.03,
    wave: 'triangle',
    accent: 1.5
  }
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
      this.master.gain.value = 0.22;
      this.master.connect(this.ctx.destination);
    }
    if (this.ctx.state === 'suspended') this.ctx.resume();
  }

  setTheme(theme) {
    if (!THEMES[theme]) return;
    if (this.theme === theme && this.timer) return;
    this.theme = theme;
    this.step = 0;
    if (this.timer) clearInterval(this.timer);
    const data = THEMES[theme];
    this.playPulse();
    this.timer = setInterval(() => this.playPulse(), data.interval);
  }

  playPulse() {
    if (!this.ctx || this.ctx.state !== 'running' || !this.theme) return;
    const data = THEMES[this.theme];
    const now = this.ctx.currentTime;
    const root = data.notes[this.step % data.notes.length];
    const next = data.notes[(this.step + 1) % data.notes.length];
    this.step += 1;

    const osc = this.ctx.createOscillator();
    const gain = this.ctx.createGain();
    osc.type = data.wave;
    osc.frequency.setValueAtTime(root, now);
    gain.gain.setValueAtTime(0.0001, now);
    gain.gain.exponentialRampToValueAtTime(data.volume, now + 0.18);
    gain.gain.exponentialRampToValueAtTime(0.0001, now + 1.25);
    osc.connect(gain).connect(this.master);
    osc.start(now);
    osc.stop(now + 1.35);

    // A quiet fifth/octave gives the game an actual musical bed rather than
    // one lonely beep wandering around the forest.
    const harmony = this.ctx.createOscillator();
    const harmonyGain = this.ctx.createGain();
    harmony.type = 'sine';
    harmony.frequency.setValueAtTime(root * 1.5, now + 0.12);
    harmonyGain.gain.setValueAtTime(0.0001, now);
    harmonyGain.gain.exponentialRampToValueAtTime(data.volume * 0.34, now + 0.3);
    harmonyGain.gain.exponentialRampToValueAtTime(0.0001, now + 1.55);
    harmony.connect(harmonyGain).connect(this.master);
    harmony.start(now);
    harmony.stop(now + 1.65);

    // A soft answering note every other step creates a recognizable motif.
    if (this.step % 2 === 0) {
      const answer = this.ctx.createOscillator();
      const answerGain = this.ctx.createGain();
      answer.type = 'sine';
      answer.frequency.value = next * data.accent;
      answerGain.gain.setValueAtTime(0.0001, now + 0.45);
      answerGain.gain.exponentialRampToValueAtTime(data.volume * 0.28, now + 0.62);
      answerGain.gain.exponentialRampToValueAtTime(0.0001, now + 1.3);
      answer.connect(answerGain).connect(this.master);
      answer.start(now + 0.45);
      answer.stop(now + 1.35);
    }
  }

  chime(kind = 'interact') {
    if (!this.ctx || this.ctx.state !== 'running') return;
    const now = this.ctx.currentTime;
    const frequencies = {
      interact: [680],
      dialogue: [520],
      clue: [523.25, 659.25],
      memory: [330, 247],
      transition: [220, 330, 440]
    };
    const sequence = frequencies[kind] || frequencies.interact;

    sequence.forEach((frequency, index) => {
      const osc = this.ctx.createOscillator();
      const gain = this.ctx.createGain();
      const when = now + index * 0.09;
      osc.type = kind === 'transition' ? 'sine' : 'triangle';
      osc.frequency.value = frequency;
      gain.gain.setValueAtTime(0.0001, when);
      gain.gain.exponentialRampToValueAtTime(kind === 'transition' ? 0.026 : 0.035, when + 0.02);
      gain.gain.exponentialRampToValueAtTime(0.0001, when + (kind === 'memory' ? 0.55 : 0.2));
      osc.connect(gain).connect(this.master);
      osc.start(when);
      osc.stop(when + 0.6);
    });
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
