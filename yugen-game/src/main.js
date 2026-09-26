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
  input: { activePointers: 3, touch: true },
  scale: {
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

/*
 * Mobile controls are installed here rather than relying on scene-local
 * touch flags. The old implementation could draw buttons without ever
 * feeding those flags into the scene's movement update loop.
 *
 * Phaser's pointer system supports multi-touch, and Arcade Physics moves
 * dynamic bodies through their velocity. We bridge the two explicitly.
 */
window.__yugenTouchVector = { x: 0, y: 0, active: false };

const originalGameUpdate = GameScene.prototype.update;
const originalLaterUpdate = LaterChaptersScene.prototype.update;

const applyTouchMovement = (scene) => {
  const input = window.__yugenTouchVector;
  if (!scene?.player?.body || !input) return;

  const blocked = Boolean(scene.dialogue?.active || scene.storyLock);
  if (blocked) {
    if (input.active) scene.player.body.setVelocity(0, 0);
    return;
  }

  if (input.active) {
    const speed = scene.playerSpeed ?? scene.speed ?? 190;
    scene.player.body.setVelocity(input.x * speed, input.y * speed);
  }
};

GameScene.prototype.update = function (time, delta) {
  if (typeof originalGameUpdate === 'function') originalGameUpdate.call(this, time, delta);
  applyTouchMovement(this);
};

LaterChaptersScene.prototype.update = function (time, delta) {
  if (typeof originalLaterUpdate === 'function') originalLaterUpdate.call(this, time, delta);
  applyTouchMovement(this);
};

// Disable the old scene-local buttons. They looked like controls but were
// not guaranteed to participate in the movement loop. One shared controller
// below is used by every playable chapter.
GameScene.prototype.buildTouchControls = function () {};
LaterChaptersScene.prototype.buildTouchControls = function () {};

const installMobileControls = () => {
  if (document.getElementById('yugen-mobile-controls')) return;
  const coarse = window.matchMedia?.('(pointer: coarse)').matches;
  const touchCapable = navigator.maxTouchPoints > 0;
  if (!coarse && !touchCapable) return;

  const host = document.getElementById('game') || document.body;
  if (getComputedStyle(host).position === 'static') host.style.position = 'relative';

  const root = document.createElement('div');
  root.id = 'yugen-mobile-controls';
  root.style.cssText = [
    'position:absolute','inset:0','z-index:9999','pointer-events:none',
    'touch-action:none','user-select:none','-webkit-user-select:none'
  ].join(';');

  const make = (tag, css, text = '') => {
    const el = document.createElement(tag);
    el.textContent = text;
    el.style.cssText = css;
    root.appendChild(el);
    return el;
  };

  const joystick = make('div', [
    'position:absolute','left:24px','bottom:24px','width:132px','height:132px',
    'border-radius:50%','background:rgba(8,12,22,.58)','border:2px solid rgba(220,226,238,.42)',
    'box-shadow:0 4px 20px rgba(0,0,0,.35)','pointer-events:auto','touch-action:none'
  ].join(';'));

  const ring = make('div', [
    'position:absolute','left:50%','top:50%','width:68px','height:68px',
    'margin:-34px','border-radius:50%','background:rgba(42,50,72,.85)',
    'border:2px solid rgba(238,241,248,.7)','box-shadow:0 2px 8px rgba(0,0,0,.4)',
    'pointer-events:none'
  ].join(';'), '');

  const setVector = (clientX, clientY) => {
    const r = joystick.getBoundingClientRect();
    const cx = r.left + r.width / 2;
    const cy = r.top + r.height / 2;
    const max = r.width * 0.36;
    let dx = clientX - cx;
    let dy = clientY - cy;
    const len = Math.hypot(dx, dy);
    if (len > max) { dx = dx / len * max; dy = dy / len * max; }
    const dead = 8;
    if (Math.hypot(dx, dy) <= dead) {
      window.__yugenTouchVector = { x: 0, y: 0, active: false };
      ring.style.transform = 'translate(-50%, -50%)';
      return;
    }
    const nx = dx / max;
    const ny = dy / max;
    window.__yugenTouchVector = { x: nx, y: ny, active: true };
    ring.style.transform = `translate(calc(-50% + ${dx}px), calc(-50% + ${dy}px))`;
  };

  const resetVector = () => {
    window.__yugenTouchVector = { x: 0, y: 0, active: false };
    ring.style.transform = 'translate(-50%, -50%)';
  };

  joystick.addEventListener('pointerdown', (e) => {
    joystick.setPointerCapture?.(e.pointerId);
    setVector(e.clientX, e.clientY);
    e.preventDefault();
  }, { passive: false });
  joystick.addEventListener('pointermove', (e) => {
    if (e.buttons || e.pressure > 0) setVector(e.clientX, e.clientY);
    e.preventDefault();
  }, { passive: false });
  ['pointerup','pointercancel','lostpointercapture'].forEach(type => joystick.addEventListener(type, resetVector));

  const buttonBase = [
    'position:absolute','width:68px','height:68px','border-radius:50%',
    'border:2px solid rgba(220,226,238,.5)','background:rgba(8,12,22,.72)',
    'color:#f4f1e8','font:600 17px sans-serif','box-shadow:0 4px 14px rgba(0,0,0,.4)',
    'pointer-events:auto','touch-action:manipulation','-webkit-tap-highlight-color:transparent'
  ].join(';');

  const action = make('button', `${buttonBase};right:28px;bottom:54px`, 'E');
  const next = make('button', `${buttonBase};right:108px;bottom:126px;width:82px;height:50px;border-radius:18px;font-size:13px`, 'NEXT');
  const label = make('div', [
    'position:absolute','left:34px','bottom:166px','color:rgba(245,244,238,.72)',
    'font:12px sans-serif','letter-spacing:1px','pointer-events:none'
  ].join(';'), 'DRAG TO MOVE');

  const activeScene = () => {
    const scenes = game?.scene?.getScenes?.(true) || [];
    return scenes.find(s => s?.player) || null;
  };

  const tap = (handler) => {
    const fn = (e) => { e.preventDefault(); e.stopPropagation(); handler(); };
    return fn;
  };

  action.addEventListener('pointerdown', tap(() => activeScene()?.handleInteract?.()), { passive: false });
  next.addEventListener('pointerdown', tap(() => {
    const scene = activeScene();
    if (scene?.dialogue?.active) scene.dialogue.advance();
  }), { passive: false });

  root.appendChild(joystick);
  // ring was already appended by make(), so it is intentionally kept as a child of root;
  // position it over the joystick after the root is attached.
  host.appendChild(root);
  joystick.appendChild(ring);

  const updateVisibility = () => {
    const visible = (window.innerWidth <= 1000) || navigator.maxTouchPoints > 0;
    root.style.display = visible ? 'block' : 'none';
  };
  updateVisibility();
  window.addEventListener('resize', updateVisibility, { passive: true });
};

let game;
try {
  game = new Phaser.Game(config);
  installMobileControls();
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
