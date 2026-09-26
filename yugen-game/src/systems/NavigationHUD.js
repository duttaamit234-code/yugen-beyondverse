import Phaser from 'phaser';
import GameScene from '../scenes/GameScene.js';
import LaterChaptersScene from '../scenes/LaterChaptersScene.js';

const TARGETS = {
  meetOldWoman: ['OLD WOMAN', 1450, 970],
  stone: ['STONE MARKER', 1595, 620],
  photograph: ['PHOTOGRAPH', 1300, 780],
  worldShift: ['VILLAGER', 1885, 1040],
  final: ['OLD WOMAN', 1450, 970],
  complete: ['VILLAGE BELL', 700, 350],
  chapter2Gate: ['FOREST GATE', 1550, 850],
  chapter2Forest: ['OLD SHRINE', 2050, 620],
  chapter2Shrine: ['MIRROR FRAGMENT', 2260, 760],
  chapter3Mirror: ['MIRROR', 2050, 620],
  chapter3Ruins: ['OLD RUINS', 2520, 1260],
  chapter4Ruins: ['THE OTHER YOU', 2520, 1370],
  chapter4Truth: ['THE OTHER YOU', 2520, 1370],
  chapter4End: ['VILLAGE BELL', 700, 350]
};

const clamp = (value, min, max) => Math.max(min, Math.min(max, value));

function getTarget(scene) {
  const stage = scene?.save?.stage || '';
  const target = TARGETS[stage];
  if (!target) return null;
  return { name: target[0], x: target[1], y: target[2] };
}

function worldToScreen(scene, x, y) {
  const camera = scene.cameras.main;
  return {
    x: (x - camera.worldView.x) * camera.zoom,
    y: (y - camera.worldView.y) * camera.zoom
  };
}

function createNavigation(scene) {
  if (scene.navHUD) return;

  const w = scene.scale.width;
  scene.navHUD = {
    panel: scene.add.rectangle(w - 20, 20, 250, 112, 0x080b13, 0.82)
      .setOrigin(1, 0).setStrokeStyle(1, 0x6f7890, 0.75).setScrollFactor(0).setDepth(130),
    title: scene.add.text(w - 34, 32, 'NEXT', {
      fontFamily: 'sans-serif', fontSize: '11px', color: '#aab4c1', letterSpacing: 2
    }).setOrigin(1, 0).setScrollFactor(0).setDepth(131),
    target: scene.add.text(w - 34, 49, '', {
      fontFamily: 'sans-serif', fontSize: '15px', color: '#f0e9d6', fontStyle: 'bold'
    }).setOrigin(1, 0).setScrollFactor(0).setDepth(131),
    arrow: scene.add.text(w - 166, 92, '➤', {
      fontFamily: 'sans-serif', fontSize: '27px', color: '#fff1b0'
    }).setOrigin(0.5).setScrollFactor(0).setDepth(131),
    distance: scene.add.text(w - 34, 92, '', {
      fontFamily: 'sans-serif', fontSize: '11px', color: '#b5bdc8'
    }).setOrigin(1, 0.5).setScrollFactor(0).setDepth(131),
    map: scene.add.graphics().setScrollFactor(0).setDepth(129),
    prompt: null,
    lastMapUpdate: 0
  };

  scene.navHUD.prompt = scene.add.text(0, 0, 'E / TAP • Interact', {
    fontFamily: 'sans-serif', fontSize: '15px', color: '#fff1b0',
    backgroundColor: '#161827', padding: { left: 12, right: 12, top: 8, bottom: 8 }
  }).setOrigin(0.5).setScrollFactor(0).setDepth(135).setVisible(false);

  layoutNavigation(scene);
}

function layoutNavigation(scene) {
  const nav = scene.navHUD;
  if (!nav) return;
  const w = scene.scale.width;
  nav.panel.setPosition(w - 18, 18);
  nav.title.setPosition(w - 34, 30);
  nav.target.setPosition(w - 34, 47);
  nav.arrow.setPosition(w - 166, 92);
  nav.distance.setPosition(w - 34, 92);
}

function updateNavigation(scene, time = 0) {
  if (!scene?.player?.body || !scene.navHUD) return;
  const nav = scene.navHUD;
  const target = getTarget(scene);

  if (!target) {
    nav.panel.setVisible(false);
    nav.prompt.setVisible(false);
    return;
  }
  nav.panel.setVisible(true);

  const dx = target.x - scene.player.x;
  const dy = target.y - scene.player.y;
  const distance = Math.round(Math.hypot(dx, dy));
  nav.target.setText(target.name);
  nav.arrow.setRotation(Math.atan2(dy, dx));
  nav.distance.setText(distance < 70 ? 'HERE' : `${distance}m`);

  if (time - nav.lastMapUpdate >= 100) {
    nav.lastMapUpdate = time;
    const mapW = 106;
    const mapH = 64;
    const left = scene.scale.width - 128;
    const top = 58;
    const g = nav.map;
    g.clear();
    g.fillStyle(0x111827, 0.8).fillRect(left, top, mapW, mapH);
    g.lineStyle(1, 0x7b8497, 0.45).strokeRect(left, top, mapW, mapH);

    const worldW = scene.worldW || 3200;
    const worldH = scene.worldH || 2200;
    const px = left + (scene.player.x / worldW) * mapW;
    const py = top + (scene.player.y / worldH) * mapH;
    const tx = left + (target.x / worldW) * mapW;
    const ty = top + (target.y / worldH) * mapH;

    g.lineStyle(2, 0xffe9ad, 0.35).lineBetween(px, py, tx, ty);
    g.fillStyle(0xeff3fa, 1).fillCircle(px, py, 3.5);
    g.fillStyle(0xffe9ad, 1).fillCircle(tx, ty, 4);
  }
}

function installInteractionFix(SceneClass) {
  const original = SceneClass.prototype.updateInteractPrompt;
  SceneClass.prototype.updateInteractPrompt = function () {
    if (!this.player || !this.interactables) return;

    let nearest = null;
    let nearestDistance = Infinity;
    for (const item of this.interactables) {
      if (!item.object?.visible && item.id !== 'oldWoman') continue;
      const x = item.object?.x ?? item.object?.list?.[0]?.x;
      const y = item.object?.y ?? item.object?.list?.[0]?.y;
      if (typeof x !== 'number' || typeof y !== 'number') continue;
      const distance = Phaser.Math.Distance.Between(this.player.x, this.player.y, x, y);
      if (distance < (this.interactDistance || 110) && distance < nearestDistance) {
        nearest = item;
        nearestDistance = distance;
      }
    }

    this.currentInteractable = nearest;
    if (!this.navHUD?.prompt) {
      if (typeof original === 'function') original.call(this);
      return;
    }

    this.interact?.setVisible(false);
    this.npcLabel?.setAlpha(0);
    this.npcPulse?.setAlpha(0);
    this.villagerLabel?.setAlpha(0);
    this.navHUD.prompt.setVisible(false);

    if (!nearest || this.dialogue?.active) return;

    const x = nearest.object?.x ?? nearest.object?.list?.[0]?.x;
    const y = nearest.object?.y ?? nearest.object?.list?.[0]?.y;
    const screen = worldToScreen(this, x, y - 62);
    const width = this.scale.width;
    const height = this.scale.height;
    this.navHUD.prompt.setPosition(
      clamp(screen.x, 110, width - 110),
      clamp(screen.y, 105, height - 230)
    ).setVisible(true);

    if (nearest.id === 'oldWoman') {
      this.npcLabel?.setAlpha(1);
      this.npcPulse?.setAlpha(this.save?.stage === 'meetOldWoman' || this.save?.stage === 'final' ? 1 : 0);
    } else if (nearest.id === 'villager') {
      this.villagerLabel?.setAlpha(this.save?.stage === 'photograph' ? 1 : 0);
    }
  };
}

function installScene(scene) {
  if (!scene || scene.navHUD) return;
  createNavigation(scene);
  const originalUpdate = scene.update;
  scene.__navigationUpdateWrapped = true;
  scene.update = function (time, delta) {
    if (typeof originalUpdate === 'function') originalUpdate.call(this, time, delta);
    updateNavigation(this, time);
  };
  scene.scale.on('resize', () => layoutNavigation(scene));
}

function patchCreate(SceneClass) {
  const originalCreate = SceneClass.prototype.create;
  if (SceneClass.prototype.__navigationCreatePatched) return;
  SceneClass.prototype.__navigationCreatePatched = true;
  SceneClass.prototype.create = function (...args) {
    const result = originalCreate.apply(this, args);
    installScene(this);
    return result;
  };
}

installInteractionFix(GameScene);
installInteractionFix(LaterChaptersScene);
patchCreate(GameScene);
patchCreate(LaterChaptersScene);
