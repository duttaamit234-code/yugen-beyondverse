import Phaser from 'phaser';

const STORY = {
  title: 'YUGEN: THE WORLD THAT REMEMBERS',
  opening: [
    { speaker: '', text: 'You wake beneath an unfamiliar sky.' },
    { speaker: '', text: 'The village ahead is quiet. Too quiet.' },
    { speaker: '', text: 'A voice whispers your name from the empty road.' },
    { speaker: '', text: 'You turn. Nobody is there.' },
    { speaker: '???', text: '“You came back.”' },
    { speaker: 'You', text: '“I have never been here.”' },
    { speaker: '???', text: 'The old woman studies you for a moment, then looks away.' }
  ],
  firstEncounter: [
    { speaker: 'Old Woman', text: '“I remember you.”' },
    { speaker: 'You', text: '“That is impossible.”' },
    { speaker: 'Old Woman', text: '“Perhaps. But that has never stopped this village from remembering.”' },
    { speaker: 'Old Woman', text: '“Go to the stone marker north of the square. Do not touch it.”' },
    { speaker: 'You', text: '“Why?”' },
    { speaker: 'Old Woman', text: '“Because last time, you did.”' }
  ],
  objectiveAfterOpening: 'Find the Old Woman at the village gate.',
  objectiveAfterEncounter: 'Find the stone marker north of the village square.'
};

export default class GameScene extends Phaser.Scene {
  constructor() {
    super('GameScene');
  }

  create() {
    this.worldW = 3200;
    this.worldH = 2200;
    this.playerSpeed = 190;
    this.interactDistance = 105;

    this.dialogue = null;
    this.dialogueQueue = [];
    this.dialogueActive = false;
    this.introComplete = false;
    this.encounterComplete = false;

    this.buildWorld();
    this.buildPlayer();
    this.buildNPC();
    this.buildUI();
    this.buildInput();
    this.buildTouchControls();

    this.physics.world.setBounds(0, 0, this.worldW, this.worldH);

    this.cameras.main.setBounds(0, 0, this.worldW, this.worldH);
    this.cameras.main.startFollow(this.player, true, 0.08, 0.08);
    this.cameras.main.setZoom(1.25);

    this.startDialogue(STORY.opening);
  }

  buildWorld() {
    const g = this.add.graphics();

    g.fillStyle(0x294632, 1);
    g.fillRect(0, 0, this.worldW, this.worldH);

    // Roads
    g.fillStyle(0x75664d, 1);
    g.fillRect(0, 980, this.worldW, 190);
    g.fillRect(1500, 0, 190, this.worldH);

    // Soft road edges
    g.lineStyle(5, 0x89785a, 0.35);
    g.lineBetween(0, 980, this.worldW, 980);
    g.lineBetween(0, 1170, this.worldW, 1170);
    g.lineBetween(1500, 0, 1500, this.worldH);
    g.lineBetween(1690, 0, 1690, this.worldH);

    // River
    g.fillStyle(0x284f68, 1);
    g.fillRect(0, 380, 1100, 150);
    g.fillRect(2180, 1670, 1020, 170);

    g.lineStyle(3, 0x4a7890, 0.6);
    for (let i = 0; i < 14; i++) {
      g.lineBetween(70 + i * 75, 425, 115 + i * 75, 425);
      g.lineBetween(2240 + i * 65, 1720, 2280 + i * 65, 1720);
    }

    // Village houses
    this.obstacles = this.physics.add.staticGroup();

    const houses = [
      [520, 760], [900, 760], [1990, 760], [2370, 760],
      [620, 1370], [1020, 1370], [2010, 1370], [2400, 1370]
    ];

    houses.forEach(([x, y], i) => {
      const body = this.add.rectangle(
        x,
        y,
        230,
        150,
        i % 2 ? 0x8b5e48 : 0x6f5545
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
    });

    // Trees
    for (let i = 0; i < 46; i++) {
      const x = Phaser.Math.Between(90, this.worldW - 90);
      const y = Phaser.Math.Between(90, this.worldH - 90);

      if (Math.abs(x - 1595) < 150 || Math.abs(y - 1075) < 125) continue;
      if (x > 1000 && x < 1120 && y > 340 && y < 570) continue;

      this.drawTree(x, y);
    }

    // First story landmark
    const monolith = this.add.rectangle(
      1595,
      620,
      42,
      150,
      0x1b2033
    ).setStrokeStyle(3, 0x8f91b5);

    this.physics.add.existing(monolith, true);
    this.obstacles.add(monolith);

    this.add.text(1595, 530, '?', {
      fontFamily: 'serif',
      fontSize: '30px',
      color: '#c7c8e8'
    }).setOrigin(0.5);

    this.add.text(1595, 760, 'STONE MARKER', {
      fontFamily: 'serif',
      fontSize: '13px',
      color: '#afb6d0'
    }).setOrigin(0.5).setAlpha(0.65);
  }

  drawTree(x, y) {
    const g = this.add.graphics();

    g.fillStyle(0x4d3427, 1);
    g.fillRect(x - 7, y + 20, 14, 38);

    g.fillStyle(0x1d3b2b, 1);
    g.fillCircle(x, y, 38);

    g.fillStyle(0x2e5835, 1);
    g.fillCircle(x - 20, y + 10, 27);
    g.fillCircle(x + 20, y + 10, 27);
  }

  buildPlayer() {
    this.player = this.add.container(1595, 1075);

    const shadow = this.add.ellipse(0, 18, 32, 12, 0x000000, 0.3);
    const body = this.add.rectangle(
      0,
      0,
      28,
      42,
      0xd7dbe8
    ).setStrokeStyle(3, 0x596178);
    const head = this.add.circle(0, -27, 12, 0xe4b28e);

    this.player.add([shadow, body, head]);

    this.physics.add.existing(this.player);
    this.player.body.setSize(24, 34);
    this.player.body.setOffset(-12, -17);
    this.player.body.setCollideWorldBounds(true);
    this.player.body.setMaxVelocity(this.playerSpeed, this.playerSpeed);
    this.player.setDepth(10);
  }

  buildNPC() {
    this.npc = this.add.container(1450, 970);

    this.npc.add(
      this.add.ellipse(0, 18, 36, 12, 0x000000, 0.25)
    );
    this.npc.add(
      this.add.rectangle(0, 0, 30, 45, 0x6d789d)
    );
    this.npc.add(
      this.add.circle(0, -29, 12, 0xd9a47f)
    );

    this.npc.setDepth(9);

    this.npcLabel = this.add.text(1450, 915, 'THE OLD WOMAN', {
      fontFamily: 'serif',
      fontSize: '15px',
      color: '#ddd7b2'
    }).setOrigin(0.5).setAlpha(0);

    this.npcPulse = this.add.circle(1450, 940, 42, 0xd8d2a3, 0.08)
      .setStrokeStyle(1, 0xd8d2a3, 0.25)
      .setAlpha(0);
  }

  buildUI() {
    this.titleText = this.add.text(
      28,
      24,
      STORY.title,
      {
        fontFamily: 'serif',
        fontSize: '22px',
        color: '#e8e4d0',
        letterSpacing: 2
      }
    ).setScrollFactor(0).setAlpha(0.9).setDepth(100);

    this.hint = this.add.text(
      28,
      55,
      'WASD / ARROWS  •  Move',
      {
        fontFamily: 'sans-serif',
        fontSize: '15px',
        color: '#b6c0c7'
      }
    ).setScrollFactor(0).setDepth(100);

    this.objectivePanel = this.add.rectangle(
      24,
      92,
      330,
      58,
      0x080b13,
      0.78
    ).setOrigin(0, 0).setStrokeStyle(1, 0x596178, 0.7)
      .setScrollFactor(0).setDepth(100);

    this.objectiveLabel = this.add.text(
      38,
      105,
      'OBJECTIVE',
      {
        fontFamily: 'sans-serif',
        fontSize: '11px',
        color: '#a7b0ba',
        letterSpacing: 1.5
      }
    ).setScrollFactor(0).setDepth(101);

    this.objectiveText = this.add.text(
      38,
      124,
      '',
      {
        fontFamily: 'sans-serif',
        fontSize: '14px',
        color: '#eee8d8',
        wordWrap: { width: 295 }
      }
    ).setScrollFactor(0).setDepth(101);

    this.dialogueBox = this.add.rectangle(
      0,
      0,
      900,
      150,
      0x080b13,
      0.94
    ).setStrokeStyle(2, 0x777a91, 0.95)
      .setScrollFactor(0)
      .setDepth(110)
      .setVisible(false)
      .setInteractive({ useHandCursor: false });

    this.speakerText = this.add.text(
      0,
      0,
      '',
      {
        fontFamily: 'sans-serif',
        fontSize: '13px',
        color: '#d6cfa5',
        letterSpacing: 1.4
      }
    ).setScrollFactor(0).setDepth(111).setVisible(false);

    this.dialogueText = this.add.text(
      0,
      0,
      '',
      {
        fontFamily: 'serif',
        fontSize: '22px',
        color: '#f2eee2',
        wordWrap: { width: 820 },
        align: 'center',
        lineSpacing: 6
      }
    ).setScrollFactor(0).setDepth(111).setOrigin(0.5).setVisible(false);

    this.continueButton = this.add.text(
      0,
      0,
      'TAP / E  •  Continue',
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
      .setInteractive({ useHandCursor: true })
      .setVisible(false);

    this.continueButton.on('pointerdown', (pointer, localX, localY, event) => {
      event.stopPropagation();
      this.advanceDialogue();
    });

    this.dialogueBox.on('pointerdown', () => this.advanceDialogue());

    this.interact = this.add.text(
      0,
      0,
      'E / TAP  •  Talk',
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
  }

  buildInput() {
    this.keys = this.input.keyboard.addKeys(
      'W,A,S,D,E,UP,DOWN,LEFT,RIGHT,SPACE'
    );

    this.input.keyboard.on('keydown-E', () => {
      if (this.dialogueActive) {
        this.advanceDialogue();
        return;
      }

      if (this.isNearNPC()) {
        this.beginNPCEncounter();
      }
    });

    this.input.keyboard.on('keydown-SPACE', () => {
      if (this.dialogueActive) this.advanceDialogue();
      else if (this.isNearNPC()) this.beginNPCEncounter();
    });
  }

  buildTouchControls() {
    this.touchState = { left: false, right: false, up: false, down: false };

    const makeButton = (x, y, label, key) => {
      const button = this.add.circle(x, y, 29, 0x101525, 0.72)
        .setStrokeStyle(1, 0x9da6b8, 0.5)
        .setScrollFactor(0)
        .setDepth(120)
        .setInteractive();

      this.add.text(x, y, label, {
        fontFamily: 'sans-serif',
        fontSize: '17px',
        color: '#f1f3f6'
      }).setOrigin(0.5).setScrollFactor(0).setDepth(121);

      const press = (pointer, localX, localY, event) => {
        event.stopPropagation();
        this.touchState[key] = true;
        button.setAlpha(1);
      };

      const release = () => {
        this.touchState[key] = false;
        button.setAlpha(0.72);
      };

      button.on('pointerdown', press);
      button.on('pointerup', release);
      button.on('pointerout', release);
    };

    this.scale.on('resize', () => {
      this.layoutUI();
      this.layoutTouchControls();
    });

    this.layoutTouchControls();
  }

  layoutTouchControls() {
    if (this.touchControlObjects) {
      this.touchControlObjects.forEach(obj => obj.destroy());
    }

    this.touchControlObjects = [];

    const w = this.scale.width;
    const h = this.scale.height;

    // Create the mobile controls only on compact screens.
    if (w > 760) return;

    const positions = [
      [w - 88, h - 140, '▲', 'up'],
      [w - 140, h - 88, '◀', 'left'],
      [w - 36, h - 88, '▶', 'right'],
      [w - 88, h - 36, '▼', 'down']
    ];

    positions.forEach(([x, y, label, key]) => {
      const button = this.add.circle(x, y, 29, 0x101525, 0.72)
        .setStrokeStyle(1, 0x9da6b8, 0.5)
        .setScrollFactor(0)
        .setDepth(120)
        .setInteractive();

      const labelText = this.add.text(x, y, label, {
        fontFamily: 'sans-serif',
        fontSize: '17px',
        color: '#f1f3f6'
      }).setOrigin(0.5).setScrollFactor(0).setDepth(121);

      const release = () => {
        this.touchState[key] = false;
        button.setAlpha(0.72);
      };

      button.on('pointerdown', (pointer, localX, localY, event) => {
        event.stopPropagation();
        this.touchState[key] = true;
        button.setAlpha(1);
      });

      button.on('pointerup', release);
      button.on('pointerout', release);

      this.touchControlObjects.push(button, labelText);
    });
  }

  layoutUI() {
    const w = this.scale.width;
    const h = this.scale.height;

    this.dialogueBox
      .setPosition(w / 2, h - 105)
      .setSize(Math.min(900, w - 32), Math.max(130, Math.min(170, h * 0.24)));

    this.speakerText.setPosition(
      w / 2 - Math.min(900, w - 32) / 2 + 24,
      h - 145
    );

    this.dialogueText.setPosition(w / 2, h - 100);

    this.continueButton.setPosition(w / 2, h - 42);
  }

  setObjective(text) {
    this.objectiveText.setText(text);
  }

  startDialogue(lines) {
    this.dialogueQueue = [...lines];
    this.dialogueActive = true;
    this.advanceDialogue();
  }

  advanceDialogue() {
    if (!this.dialogueActive) return;

    if (this.dialogueQueue.length === 0) {
      this.endDialogue();
      return;
    }

    const line = this.dialogueQueue.shift();

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

  endDialogue() {
    this.dialogueActive = false;

    this.dialogueBox.setVisible(false);
    this.speakerText.setVisible(false);
    this.dialogueText.setVisible(false);
    this.continueButton.setVisible(false);

    if (!this.introComplete) {
      this.introComplete = true;
      this.setObjective(STORY.objectiveAfterOpening);
    }
  }

  isNearNPC() {
    return Phaser.Math.Distance.Between(
      this.player.x,
      this.player.y,
      this.npc.x,
      this.npc.y
    ) < this.interactDistance;
  }

  beginNPCEncounter() {
    if (this.dialogueActive || this.encounterComplete) return;

    this.encounterComplete = true;
    this.startDialogue(STORY.firstEncounter);
  }

  update() {
    this.layoutUI();

    if (this.dialogueActive) {
      this.player.body.setVelocity(0);
      this.interact.setVisible(false);
      return;
    }

    const body = this.player.body;
    body.setVelocity(0);

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

      body.setVelocity(v.x, v.y);
    }

    this.physics.collide(this.player, this.obstacles);

    const nearNPC = this.isNearNPC();

    this.npcLabel.setAlpha(nearNPC ? 1 : 0);
    this.npcPulse.setAlpha(nearNPC && !this.encounterComplete ? 1 : 0);

    this.interact.setVisible(nearNPC && !this.encounterComplete);
    if (nearNPC && !this.encounterComplete) {
      this.interact.setPosition(this.npc.x, this.npc.y - 70);
    }

    if (nearNPC && !this.encounterComplete && this.touchState.interact) {
      this.beginNPCEncounter();
      this.touchState.interact = false;
    }

    if (this.encounterComplete && this.introComplete) {
      this.setObjective(STORY.objectiveAfterEncounter);
    }
  }
}
