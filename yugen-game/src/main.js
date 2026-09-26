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
  bootError.innerHTML = `<br><br>Yugen could not start.<br><br>${String(message).replace(/[<>&]/g, '')}`;
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
  type: Phaser.AUTO,
  parent: 'game',
  width: 1280,
  height: 720,
  backgroundColor: '#0b1020',
  pixelArt: false,
  antialias: true,
  render: { roundPixels: true },
  scale: {
    mode: Phaser.Scale.FIT,
    autoCenter: Phaser.Scale.CENTER_BOTH,
    min: { width: 360, height: 640 }
  },
  physics: {
    default: 'arcade',
    arcade: { debug: false }
  },
  scene: [GameScene, LaterChaptersScene]
};

const game = new Phaser.Game(config);

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

// Story progression is saved in localStorage. Polling here keeps the soundtrack
// synchronized even when a scene changes the stage internally.
syncMusicToSave();
setInterval(syncMusicToSave, 700);

// Small UI/gameplay sounds. Music itself remains continuous and low-volume.
window.addEventListener('keydown', (event) => {
  if (event.key === 'e' || event.key === 'E' || event.key === ' ') {
    ambientAudio.chime('interact');
  }
});
window.addEventListener('yugen-audio', (event) => {
  ambientAudio.chime(event.detail?.kind || 'dialogue');
});

const startLaterChapters = () => {
  ambientAudio.chime('transition');
  if (game.scene.isActive('GameScene')) game.scene.stop('GameScene');
  if (!game.scene.isActive('LaterChaptersScene')) {
    game.scene.start('LaterChaptersScene');
  }
};

window.addEventListener('yugen-start-chapter2', startLaterChapters);

setTimeout(() => {
  try {
    const saved = JSON.parse(localStorage.getItem('yugen-beyondverse-save-v1') || 'null');
    if (saved?.stage?.startsWith('chapter') && saved.stage !== 'chapter4Done') {
      startLaterChapters();
    }
  } catch {
    // SaveSystem handles corrupt saves.
  }
}, 0);
