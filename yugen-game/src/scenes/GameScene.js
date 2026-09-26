import Phaser from 'phaser';
import DialogueSystem from '../systems/DialogueSystem.js';
import { STORY } from '../data/story.js';
import { defaultSave, loadSave, saveGame, clearSave } from '../systems/SaveSystem.js';
import { ambientAudio } from '../systems/AmbientAudio.js';

export default class GameScene extends Phaser.Scene {
  constructor() {
    super('GameScene');
  }

  create() {
    ambientAudio.setTheme('village');
    this.worldW = 3200;
    this.worldH = 2200;
    this.playerSpeed = 190;
    this.interactDistance = 110;
    this.save = loadSave();

    this.dialogue = new DialogueSystem(this);

    this.storyLock = false;
    this.currentInteractable = null;
    this.interactables = [];

    this.buildWorld();
    this.buildPlayer();
    this.buildCharacters();
    this.buildUI();
    this.buildInput();
    this.buildTouchControls();

    this.physics.world.setBounds(0, 0, this.worldW, this.worldH);
    this.physics.add.collider(this.player, this.obstacles);

    this.cameras.main.setBounds(0, 0, this.worldW, this.worldH);
    this.cameras.main.startFollow(this.player, true, 0.08, 0.08);
    this.cameras.main.setZoom(1.25);

    this.restoreStoryState();

    if (!this.save.flags.introComplete) {
      this.startStory(STORY.opening, () => {
        this.save.flags.introComplete = true;
        this.advanceStage('meetOldWoman');
      });
    } else {
      this.setObjectiveFromStage();
    }

    window.dispatchEvent(new Event('yugen-ready'));
  }

  buildWorld() {
    const g = this.add.graphics();

    g.fillStyle(0x294632, 1);
    g.fillRect(0, 0, this.worldW, this.worldH);

    g.fillStyle(0x75664d, 1);
    g.fillRect(0, 980, this.worldW, 190);
    g.fillRect(1500, 0, 190, this.worldH);

    g.fillStyle(0x284f68, 1);
    g.fillRect(0, 380, 1100, 150);
    g.fillRect(2180, 1670, 1020, 170);

    g.lineStyle(3, 0x4a7890, 0.6);
    for (let i = 0; i < 14; i++) {
      g.lineBetween(70 + i * 75, 425, 115 + i * 75, 425);
      g.lineBetween(2240 + i * 65, 1720, 2280 + i * 65, 1720);
    }

    this.obstacles = this.physics.add.staticGroup();

    const houses = [
      [520, 760], [900, 760], [1990, 760], [2370, 760],
      [620, 1370], [1020, 1370], [2010, 1370], [2400, 1370]
    ];

    houses.forEach(([x, y], i) => this.addHouse(x, y, i));

    this.missingHouseArea = this.add.rectangle(
      1300, 760, 250, 150, 0x3d5840, 1
    ).setStrokeStyle(3, 0x7f8b6b, 0.7);

    this.missingHouseSign = this.add.text(1300, 680, 'EMPTY LOT', {
      fontFamily: 'serif',
      fontSize: '14px',
      color: '#c6cab7'
    }).setOrigin(0.5).setAlpha(0.7);

    for (let i = 0; i < 48; i++) {
      const x = Phaser.Math.Between(90, this.worldW - 90);
      const y = Phaser.Math.Between(90, this.worldH - 90);

      if (Math.abs(x - 1595) < 155 && Math.abs(y - 1075) < 130) continue;
      if (x > 980 && x < 1130 && y > 330 && y < 590) continue;
      if (x > 1200 && x < 1450 && y > 650 && y < 880) continue;

      this.drawTree(x, y);
    }

    this.createStoneMarker();
    this.createPhotoClue();

    this.shiftDecoration = this.add.rectangle(
      1760, 860, 110, 18, 0x89715b, 0.9
    ).setAlpha(0);

    this.initialTreeMarker = this.add.circle(
      1775, 900, 24, 0x355b3d, 1
    ).setAlpha(0.85);
  }
