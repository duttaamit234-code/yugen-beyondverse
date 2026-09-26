import Phaser from 'phaser';
import GameScene from './scenes/GameScene.js';
import LaterChaptersScene from './scenes/LaterChaptersScene.js';
import './style.css';

const config = {
  type: Phaser.AUTO,
  parent: 'game',
  width: 1280,
  height: 720,
  backgroundColor: '#0b1020',
  pixelArt: false,
  antialias: true,
  scale: {
    mode: Phaser.Scale.RESIZE,
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

const startLaterChapters = () => {
  if (game.scene.isActive('GameScene')) game.scene.stop('GameScene');
  if (!game.scene.isActive('LaterChaptersScene')) {
    game.scene.start('LaterChaptersScene');
  }
};

window.addEventListener('yugen-start-chapter2', startLaterChapters);

// Returning players should resume chapters 2-4 instead of being dropped
// back into the chapter 1 scene after refreshing the browser.
setTimeout(() => {
  try {
    const saved = JSON.parse(localStorage.getItem('yugen-beyondverse-save-v1') || 'null');
    if (saved?.stage?.startsWith('chapter') && saved.stage !== 'chapter4Done') {
      startLaterChapters();
    }
  } catch {
    // A corrupt save is handled by SaveSystem.
  }
}, 0);
