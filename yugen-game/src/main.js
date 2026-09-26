import Phaser from 'phaser';
import GameScene from './scenes/GameScene.js';
import LaterChaptersScene from './scenes/LaterChaptersScene.js';
import { ambientAudio } from './systems/AmbientAudio.js';
import './style.css';

const boot = document.getElementById('boot-message');
const bootError = document.getElementById('boot-error');

const showBootError = (message) => {
  if (!boot || !bootError) return;
  boot.style.display = 'grid';
  bootError.style.display = 'block';
  bootError.textContent = `Yugen could not start.\n\n${String(message || 'Unknown runtime error')}`;
  console.error('[YUGEN BOOT]', message);
};

window.addEventListener('error', (event) => {
  showBootError(event.error?.stack || event.message || 'Unknown runtime error');
});
window.addEventListener('unhandledrejection', (event) => {
  showBootError(event.reason?.stack || event.reason || 'Unhandled promise error');
});
window.addEventListener('yugen-ready', () => {
  if (boot) boot.style.display = 'none';
});

const config = {
  type: Phaser.CANVAS,
  parent: 'game',
  width: 1280,
  height: 720,
  backgroundColor: '#0b1020',
  antialias: true,
  render: { roundPixels: true },
  input: { activePointers: 2, touch: true },
  scale: {
    // RESIZE fills the phone viewport instead of letterboxing a 16:9 canvas.
    mode: Phaser.Scale.RESIZE,
    autoCenter: Phaser.Scale.CENTER_BOTH,
    expandParent: true
  },
  physics: {
    default: 'arcade',
    arcade: { debug: false }
  },
  scene: [GameScene, LaterChaptersScene]
};

let game;
try {
  game = new Phaser.Game(config);
} catch (error) {
  showBootError(error?.stack || error);
}

const themeForStage = (stage = '') => {
  if (stage.startsWith('chapter4')) return 'ruins';
  if (stage.startsWith('chapter3')) return 'shrine';
  if (stage === 'chapter2Shrine') return 'shrine';
  if (stage.startsWith('chapter2')) return 'forest';
  return 'village';
};

const syncMusicToSave = () => {
  try {
    const saved = JSON.parse(localStorage.getItem('yugen-beyondverse-save-v1') || 'null');
    ambientAudio.setTheme(themeForStage(saved?.stage || ''));
  } catch {
    ambientAudio.setTheme('village');
  }
};

ambientAudio.setTheme('village');
syncMusicToSave();
setInterval(syncMusicToSave, 700);

window.addEventListener('keydown', (event) => {
  if (event.key === 'e' || event.key === 'E' || event.key === ' ') {
    ambientAudio.chime('interact');
  }
});
window.addEventListener('yugen-audio', (event) => {
  ambientAudio.chime(event.detail?.kind || 'dialogue');
});

window.addEventListener('yugen-start-chapter2', () => {
  ambientAudio.chime('transition');
  if (!game) return;
  if (game.scene.isActive('GameScene')) game.scene.stop('GameScene');
  if (!game.scene.isActive('LaterChaptersScene')) game.scene.start('LaterChaptersScene');
});
