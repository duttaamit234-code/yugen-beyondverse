import Phaser from 'phaser';
import DialogueSystem from '../systems/DialogueSystem.js';
import { STORY } from '../data/story.js';
import { defaultSave, loadSave, saveGame, clearSave } from '../systems/SaveSystem.js';

export default class GameScene extends Phaser.Scene {
  constructor() {
    super('GameScene');
  }

  create() {
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

  addHouse(x, y, index) {
    const body = this.add.rectangle(
      x,
      y,
      230,
      150,
      index % 2 ? 0x8b5e48 : 0x6f5545
    ).setStrokeStyle(5, 0x3d2c28);

    this.physics.add.existing(body, true);
    this.obstacles.add(body);

    this.add.triangle(
      x,
      y - 100,
      0,
      100,
      115,
      0,
      230,
      100,
      0x4b3034
    );
  }

  drawTree(x, y) {
    const g = this.add.graphics();
    g.fillStyle(0x4d3427, 1).fillRect(x - 7, y + 20, 14, 38);
    g.fillStyle(0x1d3b2b, 1).fillCircle(x, y, 38);
    g.fillStyle(0x2e5835, 1)
      .fillCircle(x - 20, y + 10, 27)
      .fillCircle(x + 20, y + 10, 27);
  }

  createStoneMarker() {
    this.stone = this.add.rectangle(
      1595, 620, 42, 150, 0x1b2033
    ).setStrokeStyle(3, 0x8f91b5);

    this.physics.add.existing(this.stone, true);
    this.obstacles.add(this.stone);

    this.add.text(1595, 530, '?', {
      fontFamily: 'serif',
      fontSize: '30px',
      color: '#c7c8e8'
    }).setOrigin(0.5);

    this.add.text(1595, 760, 'STONE MARKER', {
      fontFamily: 'serif',
      fontSize: '13px',
      color: '#afb6d0'
    }).setOrigin(0.5).setAlpha(0.7);

    this.registerInteractable(
      this.stone,
      'stone',
      'Investigate the stone marker.'
    );

    this.stoneGlow = this.add.circle(
      1595, 620, 65, 0xaeb5e4, 0.06
    ).setStrokeStyle(1, 0xaeb5e4, 0.35).setAlpha(0);
  }

  createPhotoClue() {
    this.photoClue = this.add.rectangle(
      1300, 780, 28, 20, 0xded6bd, 1
    ).setStrokeStyle(2, 0x493f31);

    this.photoClueShadow = this.add.rectangle(
      1306, 786, 28, 20, 0x15171a, 0.35
    );

    this.add.text(1300, 822, 'PHOTOGRAPH', {
      fontFamily: 'serif',
      fontSize: '12px',
      color: '#d7d0bd'
    }).setOrigin(0.5).setAlpha(0);

    this.registerInteractable(
      this.photoClue,
      'photograph',
      'Inspect the photograph.'
    );
  }

  buildCharacters() {
    this.player = this.add.container(
      this.save.player.x,
      this.save.player.y
    );

    this.player.add([
      this.add.ellipse(0, 18, 32, 12, 0x000000, 0.3),
      this.add.rectangle(0, 0, 28, 42, 0xd7dbe8)
        .setStrokeStyle(3, 0x596178),
      this.add.circle(0, -27, 12, 0xe4b28e)
    ]);

    this.physics.add.existing(this.player);
    this.player.body.setSize(24, 34);
    this.player.body.setOffset(-12, -17);
    this.player.body.setCollideWorldBounds(true);
    this.player.body.setMaxVelocity(this.playerSpeed, this.playerSpeed);
    this.player.setDepth(10);

    this.oldWoman = this.add.container(1450, 970);
    this.oldWoman.add([
      this.add.ellipse(0, 18, 36, 12, 0x000000, 0.25),
      this.add.rectangle(0, 0, 30, 45, 0x6d789d),
      this.add.circle(0, -29, 12, 0xd9a47f)
    ]);
    this.oldWoman.setDepth(9);

    this.npcLabel = this.add.text(
      1450,
      915,
      'THE OLD WOMAN',
      {
        fontFamily: 'serif',
        fontSize: '15px',
        color: '#ddd7b2'
      }
    ).setOrigin(0.5).setAlpha(0);

    this.npcPulse = this.add.circle(
      1450, 940, 42, 0xd8d2a3, 0.08
    ).setStrokeStyle(1, 0xd8d2a3, 0.25).setAlpha(0);

    this.registerInteractable(
      this.oldWoman,
      'oldWoman',
      'Speak with the Old Woman.'
    );

    this.otherVillager = this.add.container(1850, 1050);
    this.otherVillager.add([
      this.add.ellipse(0, 18, 34, 11, 0x000000, 0.22),
      this.add.rectangle(0, 0, 28, 43, 0x8b795c),
      this.add.circle(0, -27, 12, 0xc99573)
    ]);
    this.otherVillager.setDepth(8);

    this.villagerLabel = this.add.text(
      1850,
      995,
      'VILLAGER',
      {
        fontFamily: 'serif',
        fontSize: '14px',
        color: '#d2c9af'
      }
    ).setOrigin(0.5).setAlpha(0);

    this.registerInteractable(
      this.otherVillager,
      'villager',
      'Ask the villager about the missing house.'
    );
  }

  buildUI() {
    this.titleText = this.add.text(
      28, 24, STORY.title,
      {
        fontFamily: 'serif',
        fontSize: '22px',
        color: '#e8e4d0',
        letterSpacing: 2
      }
    ).setScrollFactor(0).setDepth(100);

    this.hint = this.add.text(
      28, 55,
      'WASD / ARROWS • Move • E / TAP • Interact',
      {
        fontFamily: 'sans-serif',
        fontSize: '15px',
        color: '#b6c0c7'
      }
    ).setScrollFactor(0).setDepth(100);

    this.objectivePanel = this.add.rectangle(
      24, 92, 360, 68,
      0x080b13, 0.78
    ).setOrigin(0, 0)
      .setStrokeStyle(1, 0x596178, 0.7)
      .setScrollFactor(0)
      .setDepth(100);

    this.objectiveLabel = this.add.text(
      38, 105, 'OBJECTIVE',
      {
        fontFamily: 'sans-serif',
        fontSize: '11px',
        color: '#a7b0ba',
        letterSpacing: 1.5
      }
    ).setScrollFactor(0).setDepth(101);

    this.objectiveText = this.add.text(
      38, 124, '',
      {
        fontFamily: 'sans-serif',
        fontSize: '14px',
        color: '#eee8d8',
        wordWrap: { width: 320 }
      }
    ).setScrollFactor(0).setDepth(101);

    this.dialogueBox = this.add.rectangle(
      0, 0, 900, 155, 0x080b13, 0.94
    ).setStrokeStyle(2, 0x777a91, 0.95)
      .setScrollFactor(0)
      .setDepth(110)
      .setVisible(false)
      .setInteractive();

    this.speakerText = this.add.text(
      0, 0, '',
      {
        fontFamily: 'sans-serif',
        fontSize: '13px',
        color: '#d6cfa5',
        letterSpacing: 1.4
      }
    ).setScrollFactor(0).setDepth(111).setVisible(false);

    this.dialogueText = this.add.text(
      0, 0, '',
      {
        fontFamily: 'serif',
        fontSize: 22,
        color: '#f2eee2',
        wordWrap: { width: 820 },
        align: 'center',
        lineSpacing: 6
      }
    ).setScrollFactor(0).setDepth(111)
      .setOrigin(0.5)
      .setVisible(false);

    this.continueButton = this.add.text(
      0, 0,
      'TAP / E • Continue',
      {
        fontFamily: 'sans-serif',
        fontSize: '14px',
        color: '#fff1b0',
        backgroundColor: '#161827',
        padding: { left: 12, right: 12, top: 7, bottom: 7 }
      }
    ).setOrigin(0.5)
      .setScrollFactor(0)
      .setDepth(112)
      .setInteractive()
      .setVisible(false);

    this.continueButton.on('pointerdown', (pointer, x, y, event) => {
      event.stopPropagation();
      this.dialogue.advance();
    });

    this.dialogueBox.on('pointerdown', () => this.dialogue.advance());

    this.interact = this.add.text(
      0, 0,
      'E / TAP • Interact',
      {
        fontFamily: 'sans-serif',
        fontSize: '16px',
        color: '#fff1b0',
        backgroundColor: '#161827',
        padding: { left: 12, right: 12, top: 8, bottom: 8 }
      }
    ).setOrigin(0.5)
      .setScrollFactor(0)
      .setDepth(105)
      .setVisible(false);

    this.fade = this.add.rectangle(
      0, 0, 10, 10, 0x080a10, 1
    ).setOrigin(0)
      .setScrollFactor(0)
      .setDepth(200)
      .setVisible(false);

    this.memoryText = this.add.text(
      0, 0, '',
      {
        fontFamily: 'serif',
        fontSize: '28px',
        color: '#e8e3d5',
        align: 'center',
        wordWrap: { width: 760 },
        lineSpacing: 12
      }
    ).setOrigin(0.5)
      .setScrollFactor(0)
      .setDepth(201)
      .setVisible(false);

    this.toast = this.add.text(
      0, 0, '',
      {
        fontFamily: 'sans-serif',
        fontSize: '14px',
        color: '#d7dde5',
        backgroundColor: '#0c111b',
        padding: { left: 12, right: 12, top: 8, bottom: 8 }
      }
    ).setOrigin(0.5)
      .setScrollFactor(0)
      .setDepth(205)
      .setVisible(false);
  }

  buildInput() {
    this.keys = this.input.keyboard.addKeys(
      'W,A,S,D,E,UP,DOWN,LEFT,RIGHT,SPACE'
    );

    this.input.keyboard.on('keydown-E', () => this.handleInteract());
    this.input.keyboard.on('keydown-SPACE', () => this.handleInteract());

    this.input.on('pointerdown', (pointer) => {
      if (this.dialogue.active) {
        this.dialogue.advance();
        return;
      }

      if (this.currentInteractable) {
        this.handleInteract();
      }
    });
  }

  buildTouchControls() {
    this.touchState = {
      left: false,
      right: false,
      up: false,
      down: false
    };

    this.touchControlObjects = [];
    this.touchInteractButton = null;

    this.scale.on('resize', () => {
      this.layoutUI();
      this.buildTouchControls();
    });

    if (this.scale.width <= 760) {
      this.createTouchButton(
        this.scale.width - 88,
        this.scale.height - 140,
        '▲',
        'up'
      );
      this.createTouchButton(
        this.scale.width - 140,
        this.scale.height - 88,
        '◀',
        'left'
      );
      this.createTouchButton(
        this.scale.width - 36,
        this.scale.height - 88,
        '▶',
        'right'
      );
      this.createTouchButton(
        this.scale.width - 88,
        this.scale.height - 36,
        '▼',
        'down'
      );

      const button = this.createTouchButton(
        this.scale.width - 225,
        this.scale.height - 88,
        'E',
        'interact'
      );

      this.touchInteractButton = button;
    }
  }

  createTouchButton(x, y, label, key) {
    const button = this.add.circle(
      x, y, 29, 0x101525, 0.72
    ).setStrokeStyle(1, 0x9da6b8, 0.5)
      .setScrollFactor(0)
      .setDepth(120)
      .setInteractive();

    const text = this.add.text(x, y, label, {
      fontFamily: 'sans-serif',
      fontSize: '17px',
      color: '#f1f3f6'
    }).setOrigin(0.5)
      .setScrollFactor(0)
      .setDepth(121);

    const release = () => {
      if (key in this.touchState) this.touchState[key] = false;
      button.setAlpha(0.72);
    };

    button.on('pointerdown', (pointer, x2, y2, event) => {
      event.stopPropagation();

      if (key === 'interact') {
        this.handleInteract();
        button.setAlpha(1);
        this.time.delayedCall(100, () => button.setAlpha(0.72));
        return;
      }

      this.touchState[key] = true;
      button.setAlpha(1);
    });

    button.on('pointerup', release);
    button.on('pointerout', release);

    this.touchControlObjects.push(button, text);

    return button;
  }

  registerInteractable(object, id, prompt) {
    this.interactables.push({ object, id, prompt });
  }

  showDialogueLine(line) {
    this.storyLock = true;

    this.dialogueBox.setVisible(true);
    this.speakerText
      .setText(line.speaker || '')
      .setVisible(Boolean(line.speaker));
    this.dialogueText
      .setText(line.text)
      .setVisible(true);

    this.continueButton.setVisible(true);
    this.layoutUI();
  }

  hideDialogue() {
    this.dialogueBox.setVisible(false);
    this.speakerText.setVisible(false);
    this.dialogueText.setVisible(false);
    this.continueButton.setVisible(false);
    this.storyLock = false;
  }

  startStory(lines, onEnd = null) {
    this.dialogue.start(lines, onEnd);
  }

  layoutUI() {
    const w = this.scale.width;
    const h = this.scale.height;

    const boxWidth = Math.min(900, w - 32);

    this.dialogueBox
      .setPosition(w / 2, h - 105)
      .setSize(boxWidth, Math.max(135, Math.min(175, h * 0.25)));

    this.speakerText.setPosition(
      w / 2 - boxWidth / 2 + 24,
      h - 145
    );

    this.dialogueText.setPosition(w / 2, h - 101);
    this.continueButton.setPosition(w / 2, h - 38);

    this.fade.setSize(w, h);
    this.memoryText.setPosition(w / 2, h / 2);
    this.toast.setPosition(w / 2, h - 215);
  }

  setObjective(text) {
    this.objectiveText.setText(text);
  }

  setObjectiveFromStage() {
    const map = {
      meetOldWoman: STORY.objectives.meetOldWoman,
      stone: STORY.objectives.stone,
      photograph: STORY.objectives.photograph,
      worldShift: STORY.objectives.worldShift,
      final: STORY.objectives.final,
      complete: 'The village waits. Something beyond it remembers you.'
    };

    this.setObjective(map[this.save.stage] || STORY.objectives.meetOldWoman);
  }

  advanceStage(stage) {
    this.save.stage = stage;
    saveGame(this.save);
    this.setObjectiveFromStage();
  }

  restoreStoryState() {
    if (this.save.flags.stoneSeen) {
      this.stoneGlow.setAlpha(0);
    }

    if (this.save.flags.photographFound) {
      this.photoClue.setVisible(false);
      this.photoClueShadow.setVisible(false);
    }

    if (this.save.flags.villageShifted) {
      this.applyWorldShift(false);
    }
  }

  showToast(message) {
    this.toast.setText(message).setVisible(true);
    this.layoutUI();

    this.tweens.add({
      targets: this.toast,
      alpha: 1,
      duration: 150,
      hold: 1800,
      yoyo: true,
      onComplete: () => this.toast.setVisible(false)
    });
  }

  handleInteract() {
    if (this.dialogue.active || this.storyLock) {
      this.dialogue.advance();
      return;
    }

    if (!this.currentInteractable) return;

    const { id } = this.currentInteractable;

    if (id === 'oldWoman') {
      this.interactWithOldWoman();
    } else if (id === 'stone') {
      this.interactWithStone();
    } else if (id === 'villager') {
      this.interactWithVillager();
    } else if (id === 'photograph') {
      this.interactWithPhotograph();
    }
  }

  isNear(object, distance = this.interactDistance) {
    const x = object.x ?? object.list?.[0]?.x;
    const y = object.y ?? object.list?.[0]?.y;

    return Phaser.Math.Distance.Between(
      this.player.x,
      this.player.y,
      x,
      y
    ) <= distance;
  }

  interactWithOldWoman() {
    if (this.save.stage === 'meetOldWoman') {
      this.startStory(STORY.oldWomanFirst, () => {
        this.save.flags.oldWomanMet = true;
        this.advanceStage('stone');
      });
      return;
    }

    if (
      this.save.stage === 'final' &&
      !this.save.flags.oldWomanSecondMet
    ) {
      this.startStory(STORY.oldWomanSecond, () => {
        this.save.flags.oldWomanSecondMet = true;
        this.advanceStage('complete');
      });
      return;
    }

    this.showToast('The Old Woman watches you in silence.');
  }

  interactWithStone() {
    if (this.save.stage !== 'stone' || this.save.flags.stoneSeen) {
      this.showToast('The stone feels cold beneath your hand.');
      return;
    }

    this.save.flags.stoneSeen = true;
    saveGame(this.save);

    this.startMemorySequence(() => {
      this.advanceStage('photograph');
    });
  }

  startMemorySequence(onComplete) {
    this.storyLock = true;
    this.fade.setVisible(true).setAlpha(0);

    const camera = this.cameras.main;
    const originalZoom = camera.zoom;

    this.tweens.add({
      targets: this.fade,
      alpha: 1,
      duration: 500,
      onComplete: () => {
        this.memoryText
          .setText(
            'The village disappears.\n\nThe sky is red.\n\nSomeone who looks exactly like you stands beside the stone.'
          )
          .setVisible(true)
          .setAlpha(0);

        this.tweens.add({
          targets: this.memoryText,
          alpha: 1,
          duration: 700,
          hold: 1800,
          yoyo: true,
          onComplete: () => {
            this.memoryText.setVisible(false);

            this.tweens.add({
              targets: this.fade,
              alpha: 0,
              duration: 650,
              onComplete: () => {
                this.fade.setVisible(false);
                camera.setZoom(originalZoom);
                this.storyLock = false;

                this.startStory(STORY.stone, onComplete);
              }
            });
          }
        });
      }
    });

    camera.setZoom(1.38);
  }

  interactWithVillager() {
    if (this.save.stage !== 'photograph') {
      this.showToast('The villager avoids your eyes.');
      return;
    }

    this.startStory(STORY.missingHouse, () => {
      this.advanceStage('worldShift');
    });
  }

  interactWithPhotograph() {
    if (this.save.stage !== 'photograph') {
      this.showToast('There is nothing here that needs your attention.');
      return;
    }

    this.save.flags.photographFound = true;
    saveGame(this.save);

    this.photoClue.setVisible(false);
    this.photoClueShadow.setVisible(false);

    this.showToast('A photograph from seventeen years ago.');

    this.startStory(
      [
        { speaker: '', text: 'The photograph shows the village as it is now.' },
        { speaker: '', text: 'The Old Woman is there.' },
        { speaker: '', text: 'The other villagers are there.' },
        { speaker: 'You', text: '“And me.”' },
        { speaker: '', text: 'Your name is written on the back.' },
        { speaker: '', text: 'There is no date. Only a single sentence:' },
        { speaker: 'Unknown', text: '“If you are reading this, the village has forgotten again.”' }
      ],
      () => {
        this.applyWorldShift(true);
        this.advanceStage('worldShift');
      }
    );
  }

  applyWorldShift(persist) {
    if (this.save.flags.villageShifted && !persist) {
      this.otherVillager.setPosition(1885, 1040);
      this.villagerLabel.setPosition(1885, 985);
      this.initialTreeMarker.setVisible(false);
      this.shiftDecoration.setVisible(true).setAlpha(1);
      return;
    }

    this.save.flags.villageShifted = true;

    // The village should feel different without requiring a huge new map.
    this.otherVillager.setPosition(1885, 1040);
    this.villagerLabel.setPosition(1885, 985);

    this.initialTreeMarker.setVisible(false);
    this.shiftDecoration.setVisible(true).setAlpha(1);

    if (persist) {
      saveGame(this.save);
    }

    this.startStory(STORY.worldShift, () => {
      this.advanceStage('final');

      this.startStory(
        STORY.oldWomanSecond,
        () => {
          this.save.flags.oldWomanSecondMet = true;
          this.advanceStage('complete');
        }
      );
    });
  }

  update() {
    if (!this.player?.body) return;

    this.layoutUI();

    if (this.dialogue.active || this.storyLock) {
      this.player.body.setVelocity(0);
      this.updateInteractPrompt();
      return;
    }

    let x = 0;
    let y = 0;

    if (this.keys.A.isDown || this.keys.LEFT.isDown || this.touchState.left) x -= 1;
    if (this.keys.D.isDown || this.keys.RIGHT.isDown || this.touchState.right) x += 1;
    if (this.keys.W.isDown || this.keys.UP.isDown || this.touchState.up) y -= 1;
    if (this.keys.S.isDown || this.keys.DOWN.isDown || this.touchState.down) y += 1;

    if (x || y) {
      const v = new Phaser.Math.Vector2(x, y)
        .normalize()
        .scale(this.playerSpeed);

      this.player.body.setVelocity(v.x, v.y);
    } else {
      this.player.body.setVelocity(0);
    }

    this.updateInteractPrompt();
    this.savePlayerPosition();
  }

  updateInteractPrompt() {
    if (!this.interactables) return;

    let nearest = null;
    let nearestDistance = Infinity;

    for (const item of this.interactables) {
      if (!item.object.visible && item.id !== 'oldWoman') continue;

      const x = item.object.x ?? item.object.list?.[0]?.x;
      const y = item.object.y ?? item.object.list?.[0]?.y;
      if (typeof x !== 'number' || typeof y !== 'number') continue;

      const distance = Phaser.Math.Distance.Between(
        this.player.x,
        this.player.y,
        x,
        y
      );

      if (distance < this.interactDistance && distance < nearestDistance) {
        nearest = item;
        nearestDistance = distance;
      }
    }

    this.currentInteractable = nearest;

    if (!nearest) {
      this.interact.setVisible(false);
      this.npcLabel.setAlpha(0);
      this.npcPulse.setAlpha(0);
      this.villagerLabel.setAlpha(0);
      return;
    }

    this.interact
      .setText('E / TAP • Interact')
      .setVisible(!this.dialogue.active);

    const x = nearest.object.x ?? nearest.object.list?.[0]?.x;
    const y = nearest.object.y ?? nearest.object.list?.[0]?.y;

    this.interact.setPosition(x, y - 72);

    if (nearest.id === 'oldWoman') {
      this.npcLabel.setAlpha(1);
      this.npcPulse.setAlpha(this.save.stage === 'meetOldWoman' || this.save.stage === 'final' ? 1 : 0);
    } else if (nearest.id === 'villager') {
      this.villagerLabel.setAlpha(this.save.stage === 'photograph' ? 1 : 0);
    }
  }

  savePlayerPosition() {
    if (!this.time.now || Math.floor(this.time.now) % 120 !== 0) return;

    this.save.player.x = Math.round(this.player.x);
    this.save.player.y = Math.round(this.player.y);
    saveGame(this.save);
  }

  restoreStoryState() {
    if (this.save.flags.photographFound) {
      this.photoClue.setVisible(false);
      this.photoClueShadow.setVisible(false);
    }

    if (this.save.flags.villageShifted) {
      this.applyWorldShift(false);
    }

    this.setObjectiveFromStage();
  }

  shutdown() {
    this.save.player.x = Math.round(this.player.x);
    this.save.player.y = Math.round(this.player.y);
    saveGame(this.save);
  }
}
