import Phaser from 'phaser';

const STORY = {
  title: 'YUGEN: THE WORLD THAT REMEMBERS',
  opening: [
    'You wake beneath an unfamiliar sky.',
    'The village ahead is quiet. Too quiet.',
    'A voice whispers your name from the empty road.',
    'You turn. Nobody is there.',
    'Then an old woman at the gate looks directly at you.',
    '“You came back.”',
    'You have never seen her before.'
  ]
};

export default class GameScene extends Phaser.Scene {
  constructor() { super('GameScene'); }

  create() {
    this.cameras.main.setBackgroundColor('#0b1020');
    this.worldW = 3200;
    this.worldH = 2200;
    this.playerSpeed = 190;
    this.interactDistance = 90;
    this.storyStarted = false;
    this.dialogueIndex = 0;

    this.buildWorld();
    this.buildPlayer();
    this.buildNPC();
    this.buildUI();
    this.buildInput();

    this.cameras.main.startFollow(this.player, true, 0.08, 0.08);
    this.cameras.main.setBounds(0, 0, this.worldW, this.worldH);

    this.showDialogue(STORY.opening[0]);
  }

  buildWorld() {
    const g = this.add.graphics();
    g.fillStyle(0x294632, 1).fillRect(0, 0, this.worldW, this.worldH);

    // Roads
    g.fillStyle(0x75664d, 1);
    g.fillRect(0, 980, this.worldW, 190);
    g.fillRect(1500, 0, 190, this.worldH);

    // River
    g.fillStyle(0x284f68, 1);
    g.fillRect(0, 380, 1100, 150);
    g.fillRect(2180, 1670, 1020, 170);

    // Village houses and fences
    this.obstacles = this.physics.add.staticGroup();
    const houses = [
      [520, 760], [900, 760], [1990, 760], [2370, 760],
      [620, 1370], [1020, 1370], [2010, 1370], [2400, 1370]
    ];
    houses.forEach(([x, y], i) => {
      const body = this.add.rectangle(x, y, 230, 150, i % 2 ? 0x8b5e48 : 0x6f5545).setStrokeStyle(5, 0x3d2c28);
      this.physics.add.existing(body, true);
      this.obstacles.add(body);
      this.add.triangle(x, y - 100, 0, 100, 115, 0, 230, 100, 0x4b3034);
    });

    for (let i = 0; i < 46; i++) {
      const x = Phaser.Math.Between(90, this.worldW - 90);
      const y = Phaser.Math.Between(90, this.worldH - 90);
      if (Math.abs(x - 1595) < 150 || Math.abs(y - 1075) < 120) continue;
      this.drawTree(x, y);
    }

    // Strange monolith: first mystery landmark
    const monolith = this.add.rectangle(1595, 550, 42, 150, 0x1b2033).setStrokeStyle(3, 0x8f91b5);
    this.physics.add.existing(monolith, true);
    this.obstacles.add(monolith);
    this.add.text(1595, 470, '?', { fontFamily: 'serif', fontSize: '30px', color: '#c7c8e8' }).setOrigin(0.5);
  }

  drawTree(x, y) {
    const g = this.add.graphics();
    g.fillStyle(0x4d3427, 1).fillRect(x - 7, y + 20, 14, 38);
    g.fillStyle(0x1d3b2b, 1).fillCircle(x, y, 38);
    g.fillStyle(0x2e5835, 1).fillCircle(x - 20, y + 10, 27).fillCircle(x + 20, y + 10, 27);
  }

  buildPlayer() {
    this.player = this.add.container(1595, 1075);
    const shadow = this.add.ellipse(0, 18, 32, 12, 0x000000, 0.3);
    const body = this.add.rectangle(0, 0, 28, 42, 0xd7dbe8).setStrokeStyle(3, 0x596178);
    const head = this.add.circle(0, -27, 12, 0xe4b28e);
    this.player.add([shadow, body, head]);
    this.physics.add.existing(this.player);
    this.player.body.setSize(24, 34);
    this.player.body.setOffset(-12, -17);
  }

  buildNPC() {
    this.npc = this.add.container(1450, 970);
    this.npc.add(this.add.ellipse(0, 18, 36, 12, 0x000000, 0.25));
    this.npc.add(this.add.rectangle(0, 0, 30, 45, 0x6d789d));
    this.npc.add(this.add.circle(0, -29, 12, 0xd9a47f));
    this.npcLabel = this.add.text(1450, 915, 'THE OLD WOMAN', {
      fontFamily: 'serif', fontSize: '15px', color: '#ddd7b2'
    }).setOrigin(0.5).setAlpha(0);
  }

  buildUI() {
    this.titleText = this.add.text(28, 24, STORY.title, {
      fontFamily: 'serif', fontSize: '22px', color: '#e8e4d0', letterSpacing: 2
    }).setScrollFactor(0).setAlpha(0.9);

    this.hint = this.add.text(28, 55, 'WASD / ARROWS  •  Move', {
      fontFamily: 'sans-serif', fontSize: '15px', color: '#b6c0c7'
    }).setScrollFactor(0);

    this.dialogueBox = this.add.rectangle(0, 0, 900, 125, 0x080b13, 0.92)
      .setStrokeStyle(2, 0x777a91).setScrollFactor(0).setVisible(false);
    this.dialogue = this.add.text(0, 0, '', {
      fontFamily: 'serif', fontSize: '22px', color: '#f2eee2',
      wordWrap: { width: 820 }, align: 'center'
    }).setScrollFactor(0).setOrigin(0.5).setVisible(false);

    this.interact = this.add.text(0, 0, 'E / TAP  •  Interact', {
      fontFamily: 'sans-serif', fontSize: '16px', color: '#fff1b0',
      backgroundColor: '#161827', padding: { left: 12, right: 12, top: 8, bottom: 8 }
    }).setOrigin(0.5).setScrollFactor(0).setVisible(false);
  }

  buildInput() {
    this.keys = this.input.keyboard.addKeys('W,A,S,D,E,UP,DOWN,LEFT,RIGHT,SPACE');
    this.input.on('pointerdown', () => this.tryAdvanceDialogue());
  }

  showDialogue(text) {
    this.dialogueBox.setVisible(true);
    this.dialogue.setText(text).setVisible(true);
    this.positionDialogue();
  }

  positionDialogue() {
    const w = this.scale.width;
    const h = this.scale.height;
    this.dialogueBox.setPosition(w / 2, h - 100).setSize(Math.min(900, w - 32), 125);
    this.dialogue.setPosition(w / 2, h - 100);
  }

  tryAdvanceDialogue() {
    if (!this.dialogue.visible) return;
    this.dialogueIndex++;
    if (this.dialogueIndex < STORY.opening.length) {
      this.showDialogue(STORY.opening[this.dialogueIndex]);
    } else {
      this.dialogue.setVisible(false);
      this.dialogueBox.setVisible(false);
      this.storyStarted = true;
    }
  }

  update() {
    this.positionDialogue();
    const body = this.player.body;
    body.setVelocity(0);

    let x = 0, y = 0;
    if (this.keys.A.isDown || this.keys.LEFT.isDown) x -= 1;
    if (this.keys.D.isDown || this.keys.RIGHT.isDown) x += 1;
    if (this.keys.W.isDown || this.keys.UP.isDown) y -= 1;
    if (this.keys.S.isDown || this.keys.DOWN.isDown) y += 1;

    if (x || y) {
      const v = new Phaser.Math.Vector2(x, y).normalize().scale(this.playerSpeed);
      body.setVelocity(v.x, v.y);
    }

    this.physics.collide(this.player, this.obstacles);

    const d = Phaser.Math.Distance.Between(this.player.x, this.player.y, this.npc.x, this.npc.y);
    const nearNPC = d < this.interactDistance;
    this.npcLabel.setAlpha(nearNPC ? 1 : 0);
    this.interact.setVisible(nearNPC && this.storyStarted);
    if (nearNPC) {
      this.interact.setPosition(this.npc.x, this.npc.y - 70);
      if (Phaser.Input.Keyboard.JustDown(this.keys.E) || Phaser.Input.Keyboard.JustDown(this.keys.SPACE)) {
        this.showDialogue('“I remember you.”\n“Why do you keep pretending you do not remember me?”');
        this.storyStarted = false;
      }
    }
  }
}
