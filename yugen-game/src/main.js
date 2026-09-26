import Phaser from 'phaser';
import GameScene from './scenes/GameScene.js';
import LaterChaptersScene from './scenes/LaterChaptersScene.js';
import { ambientAudio } from './systems/AmbientAudio.js';
import './style.css';

const boot = document.getElementById('boot-message');
const bootError = document.getElementById('boot-error');
const rotateOverlay = document.getElementById('rotate-overlay');
const rotateButton = document.getElementById('rotate-button');

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
  input: { activePointers: 3, touch: true },
  scale: {
    // Keep a predictable 16:9 landscape game surface. Portrait phones
    // display the rotate screen instead of squeezing the game into a strip.
    mode: Phaser.Scale.FIT,
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
window.__yugenTouchVector = { x: 0, y: 0, active: false };

const applyTouchMovement = (scene) => {
  const input = window.__yugenTouchVector;
  if (!scene?.player?.body || !input?.active) return;

  if (scene.dialogue?.active || scene.storyLock) {
    scene.player.body.setVelocity(0, 0);
    return;
  }

  const speed = scene.playerSpeed ?? scene.speed ?? 190;
  scene.player.body.setVelocity(input.x * speed, input.y * speed);
};

const wrapSceneUpdate = (SceneClass) => {
  const original = SceneClass.prototype.update;
  SceneClass.prototype.update = function (time, delta) {
    if (typeof original === 'function') original.call(this, time, delta);
    applyTouchMovement(this);
  };
};

wrapSceneUpdate(GameScene);
wrapSceneUpdate(LaterChaptersScene);

// The scene-local controller is intentionally disabled. There is one shared
// viewport controller so Chapters 1-4 use identical, testable touch input.
GameScene.prototype.buildTouchControls = function () {};
LaterChaptersScene.prototype.buildTouchControls = function () {};

const activeScene = () => {
  const scenes = game?.scene?.getScenes?.(true) || [];
  return scenes.find((scene) => scene && scene.player) || null;
};

const installMobileControls = () => {
  if (document.getElementById('yugen-mobile-controls')) return;

  const coarse = window.matchMedia?.('(pointer: coarse)').matches ?? false;
  const touchCapable = navigator.maxTouchPoints > 0;
  if (!coarse && !touchCapable) return;

  const host = document.getElementById('game') || document.body;
  if (getComputedStyle(host).position === 'static') host.style.position = 'relative';

  const root = document.createElement('div');
  root.id = 'yugen-mobile-controls';
  root.innerHTML = `
    <div id="yugen-stick-base" aria-label="Move joystick">
      <span class="yugen-stick-label">MOVE</span>
      <div id="yugen-stick-knob"></div>
    </div>
    <button id="yugen-action-e" class="yugen-action" type="button" aria-label="Interact">E</button>
    <button id="yugen-action-next" class="yugen-action yugen-next" type="button" aria-label="Next dialogue">NEXT</button>
    <div class="yugen-control-hint">DRAG TO MOVE · E INTERACT · NEXT DIALOGUE</div>
  `;

  host.appendChild(root);

  const joystick = document.getElementById('yugen-stick-base');
  const knob = document.getElementById('yugen-stick-knob');
  const actionE = document.getElementById('yugen-action-e');
  const actionNext = document.getElementById('yugen-action-next');

  let pointerId = null;
  const maxDistance = 44;

  const setVector = (clientX, clientY) => {
    const rect = joystick.getBoundingClientRect();
    const cx = rect.left + rect.width / 2;
    const cy = rect.top + rect.height / 2;

    let dx = clientX - cx;
    let dy = clientY - cy;
    const distance = Math.hypot(dx, dy);

    if (distance > maxDistance) {
      dx = (dx / distance) * maxDistance;
      dy = (dy / distance) * maxDistance;
    }

    knob.style.transform = `translate(${dx}px, ${dy}px)`;

    const nx = dx / maxDistance;
    const ny = dy / maxDistance;
    const length = Math.hypot(nx, ny);

    if (length < 0.16) {
      window.__yugenTouchVector = { x: 0, y: 0, active: false };
      return;
    }

    // Normalize so diagonal travel isn't faster than cardinal travel.
    const scale = Math.min(1, 1 / length);
    window.__yugenTouchVector = {
      x: nx * scale,
      y: ny * scale,
      active: true
    };
  };

  const reset = () => {
    pointerId = null;
    knob.style.transform = 'translate(0, 0)';
    window.__yugenTouchVector = { x: 0, y: 0, active: false };
  };

  joystick.addEventListener('pointerdown', (event) => {
    event.preventDefault();
    event.stopPropagation();
    pointerId = event.pointerId;
    joystick.setPointerCapture?.(pointerId);
    setVector(event.clientX, event.clientY);
  }, { passive: false });

  joystick.addEventListener('pointermove', (event) => {
    if (event.pointerId !== pointerId) return;
    event.preventDefault();
    setVector(event.clientX, event.clientY);
  }, { passive: false });

  joystick.addEventListener('pointerup', reset);
  joystick.addEventListener('pointercancel', reset);
  joystick.addEventListener('lostpointercapture', reset);

  const interact = (button, callback) => {
    button.addEventListener('pointerdown', (event) => {
      event.preventDefault();
      event.stopPropagation();
      button.classList.add('pressed');
      callback();
    }, { passive: false });
    ['pointerup', 'pointercancel', 'pointerleave'].forEach((type) => {
      button.addEventListener(type, () => button.classList.remove('pressed'));
    });
  };

  interact(actionE, () => activeScene()?.handleInteract?.());
  interact(actionNext, () => {
    const scene = activeScene();
    if (scene?.dialogue?.active) scene.dialogue.advance();
  });

  const syncControls = () => {
    const portrait = window.innerHeight > window.innerWidth;
    root.classList.toggle('hidden', portrait);
  };

  syncControls();
  window.addEventListener('resize', syncControls, { passive: true });
  window.addEventListener('orientationchange', syncControls, { passive: true });
  window.addEventListener('blur', reset);
  document.addEventListener('visibilitychange', () => {
    if (document.hidden) reset();
  });
};

const refreshOrientation = () => {
  const portrait = window.innerHeight > window.innerWidth;
  rotateOverlay?.classList.toggle('visible', portrait);
};

const requestLandscape = async () => {
  try {
    await document.documentElement.requestFullscreen?.();
  } catch {
    // Fullscreen is optional. The overlay still guides the user to rotate.
  }

  try {
    await screen.orientation?.lock?.('landscape');
  } catch {
    // Browsers may reject orientation locking unless fullscreen is active.
  }

  refreshOrientation();
};

rotateButton?.addEventListener('click', requestLandscape, { passive: true });
window.addEventListener('resize', refreshOrientation, { passive: true });
window.addEventListener('orientationchange', refreshOrientation, { passive: true });

try {
  game = new Phaser.Game(config);
  installMobileControls();
  refreshOrientation();
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
