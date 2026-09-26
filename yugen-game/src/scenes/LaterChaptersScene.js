import Phaser from 'phaser';
import DialogueSystem from '../systems/DialogueSystem.js';
import { STORY } from '../data/story.js';
import { loadSave, saveGame } from '../systems/SaveSystem.js';

export default class LaterChaptersScene extends Phaser.Scene {
  constructor() {
    super('LaterChaptersScene');
  }

  create() {
    this.save = loadSave();
    this.dialogue = new DialogueSystem(this);
    this.storyLock = false;
    this.currentInteractable = null;
    this.interactables = [];
    this.speed = 190;
    this.worldW = 3000;
    this.worldH = 2000;

    this.buildWorld();
    this.buildPlayer();
    this.buildUI();
    this.buildInput();
    this.buildTouchControls();

    this.physics.world.setBounds(0, 0, this.worldW, this.worldH);
    this.physics.add.collider(this.player, this.obstacles);
    this.cameras.main.setBounds(0, 0, this.worldW, this.worldH);
    this.cameras.main.startFollow(this.player, true, 0.08, 0.08);
    this.cameras.main.setZoom(1.2);

    this.setStagePresentation();
  }

  buildWorld() {
    const g = this.add.graphics();
    g.fillStyle(0x162c27, 1).fillRect(0, 0, this.worldW, this.worldH);

    g.fillStyle(0x554d42, 1).fillRect(0, 850, this.worldW, 150);
    g.fillStyle(0x304d3d, 1).fillRect(1150, 0, 170, this.worldH);
    g.fillStyle(0x20252f, 1).fillRect(2200, 0, 800, this.worldH);

    this.obstacles = this.physics.add.staticGroup();

    for (let i = 0; i < 55; i++) {
      const x = Phaser.Math.Between(80, 2120);
      const y = Phaser.Math.Between(80, 1900);
      if (Math.abs(x - 500) < 220 && Math.abs(y - 900) < 180) continue;
      if (Math.abs(x - 1550) < 240 && Math.abs(y - 850) < 180) continue;
      this.tree(x, y);
    }

    this.oldWoman = this.npc(500, 850, 0x6d789d, 0xd9a47f);
    this.add.text(500, 785, 'THE OLD WOMAN', {
      fontFamily: 'serif', fontSize: '15px', color: '#ddd7b2'
    }).setOrigin(0.5).setAlpha(0.9);
    this.register(this.oldWoman, 'oldWoman');

    this.gate = this.add.rectangle(1550, 850, 100, 210, 0x111d1b)
      .setStrokeStyle(4, 0x718d77);
    this.add.text(1550, 715, 'FOREST PATH', {
      fontFamily: 'serif', fontSize: '14px', color: '#c3d0bf'
    }).setOrigin(0.5);
    this.register(this.gate, 'gate');

    this.shrine = this.add.rectangle(2050, 620, 150, 120, 0x514653)
      .setStrokeStyle(4, 0xa28fa7);
    this.add.triangle(2050, 510, 0, 100, 75, 0, 150, 100, 0x332b38);
    this.add.text(2050, 750, 'OLD SHRINE', {
      fontFamily: 'serif', fontSize: '14px', color: '#d0c3d7'
    }).setOrigin(0.5);
    this.register(this.shrine, 'shrine');

    this.mirror = this.add.rectangle(2050, 620, 72, 88, 0x95a2b5, 0.7)
      .setStrokeStyle(3, 0xd7d9e8).setVisible(true);
    this.add.text(2050, 675, '◇', {
      fontFamily: 'serif', fontSize: '38px', color: '#f0edf7'
    }).setOrigin(0.5);

    this.fragment = this.add.triangle(2260, 760, 0, 48, 24, 0, 48, 48, 0xb7bdd0)
      .setStrokeStyle(2, 0xeee8ff);
    this.add.text(2260, 820, 'MIRROR FRAGMENT', {
      fontFamily: 'serif', fontSize: '11px', color: '#c7c4d4'
    }).setOrigin(0.5).setAlpha(0.8);
    this.register(this.fragment, 'fragment');

    this.ruins = this.add.rectangle(2520, 1260, 310, 260, 0x34333b)
      .setStrokeStyle(5, 0x77727e);
    this.add.text(2520, 1070, 'THE OLD RUINS', {
      fontFamily: 'serif', fontSize: '17px', color: '#c7c0c8'
    }).setOrigin(0.5);
    this.register(this.ruins, 'ruins');

    this.otherYou = this.npc(2520, 1370, 0x8e5360, 0xd9a47f);
    this.add.text(2520, 1305, '???', {
      fontFamily: 'serif', fontSize: '18px', color: '#e7cbd0'
    }).setOrigin(0.5).setAlpha(0);
    this.register(this.otherYou, 'otherYou');

    this.returnBell = this.add.circle(700, 350, 34, 0x918d7b)
      .setStrokeStyle(3, 0xd6d0b4);
    this.add.text(700, 405, 'VILLAGE BELL', {
      fontFamily: 'serif', fontSize: '12px', color: '#d1ccb8'
    }).setOrigin(0.5);
    this.register(this.returnBell, 'bell');
  }

  tree(x, y) {
    this.add.rectangle(x, y + 20, 14, 40, 0x49382c);
    this.add.circle(x, y, 40, 0x1b392c);
    this.add.circle(x - 20, y + 10, 27, 0x28503a);
    this.add.circle(x + 20, y + 10, 27, 0x28503a);
  }

  npc(x, y, bodyColor, skinColor) {
    const c = this.add.container(x, y);
    c.add([
      this.add.ellipse(0, 18, 36, 12, 0x000000, 0.28),
      this.add.rectangle(0, 0, 30, 45, bodyColor),
      this.add.circle(0, -29, 12, skinColor)
    ]);
    c.setDepth(10);
    return c;
  }

  buildPlayer() {
    const p = this.save.player || { x: 650, y: 900 };
    this.player = this.add.container(
      this.save.stage === 'chapter2Gate' ? 650 : 1450,
      this.save.stage === 'chapter2Gate' ? 900 : 850
    );
    this.player.add([
      this.add.ellipse(0, 18, 32, 12, 0x000000, 0.3),
      this.add.rectangle(0, 0, 28, 42, 0xd7dbe8).setStrokeStyle(3, 0x596178),
      this.add.circle(0, -27, 12, 0xe4b28e)
    ]);
    this.physics.add.existing(this.player);
    this.player.body.setSize(24, 34);
    this.player.body.setOffset(-12, -17);
    this.player.body.setCollideWorldBounds(true);
    this.player.body.setMaxVelocity(this.speed, this.speed);
    this.player.setDepth(20);
  }

  buildUI() {
    this.chapterText = this.add.text(28, 24, '', {
      fontFamily: 'serif', fontSize: '23px', color: '#e8e4d0', letterSpacing: 2
    }).setScrollFactor(0).setDepth(100);

    this.objective = this.add.text(28, 62, '', {
      fontFamily: 'sans-serif', fontSize: '15px', color: '#d5dbe0',
      wordWrap: { width: 430 }
    }).setScrollFactor(0).setDepth(100);

    this.dialogueBox = this.add.rectangle(0, 0, 900, 155, 0x080b13, 0.95)
      .setStrokeStyle(2, 0x777a91).setScrollFactor(0).setDepth(110)
      .setVisible(false).setInteractive();
    this.speaker = this.add.text(0, 0, '', {
      fontFamily: 'sans-serif', fontSize: '13px', color: '#d6cfa5', letterSpacing: 1.4
    }).setScrollFactor(0).setDepth(111).setVisible(false);
    this.dialogueText = this.add.text(0, 0, '', {
      fontFamily: 'serif', fontSize: 22, color: '#f2eee2',
      wordWrap: { width: 820 }, align: 'center', lineSpacing: 6
    }).setOrigin(0.5).setScrollFactor(0).setDepth(111).setVisible(false);
    this.continueButton = this.add.text(0, 0, 'TAP / E • Continue', {
      fontFamily: 'sans-serif', fontSize: '14px', color: '#fff1b0',
      backgroundColor: '#161827', padding: { left: 12, right: 12, top: 7, bottom: 7 }
    }).setOrigin(0.5).setScrollFactor(0).setDepth(112).setInteractive().setVisible(false);
    this.continueButton.on('pointerdown', (p, x, y, e) => {
      e.stopPropagation(); this.dialogue.advance();
    });
    this.dialogueBox.on('pointerdown', () => this.dialogue.advance());

    this.interact = this.add.text(0, 0, 'E / TAP • Interact', {
      fontFamily: 'sans-serif', fontSize: '16px', color: '#fff1b0',
      backgroundColor: '#161827', padding: { left: 12, right: 12, top: 8, bottom: 8 }
    }).setOrigin(0.5).setScrollFactor(0).setDepth(105).setVisible(false);

    this.endCard = this.add.text(0, 0, '', {
      fontFamily: 'serif', fontSize: 26, color: '#eee9dc', align: 'center',
      wordWrap: { width: 760 }, lineSpacing: 12
    }).setOrigin(0.5).setScrollFactor(0).setDepth(200).setVisible(false);
  }

  buildInput() {
    this.keys = this.input.keyboard.addKeys('W,A,S,D,E,UP,DOWN,LEFT,RIGHT,SPACE');
    this.input.keyboard.on('keydown-E', () => this.handleInteract());
    this.input.keyboard.on('keydown-SPACE', () => this.handleInteract());
    this.input.on('pointerdown', () => {
      if (!this.dialogue.active && this.currentInteractable) this.handleInteract();
    });
  }

  buildTouchControls() {
    this.touch = { left: false, right: false, up: false, down: false };
    this.touchObjects = [];
    if (this.scale.width > 760) return;
    const w = this.scale.width, h = this.scale.height;
    [['▲','up',w-88,h-140],['◀','left',w-140,h-88],['▶','right',w-36,h-88],['▼','down',w-88,h-36],['E','interact',w-225,h-88]].forEach(([label,key,x,y]) => {
      const b = this.add.circle(x,y,29,0x101525,0.72).setStrokeStyle(1,0x9da6b8,0.5).setScrollFactor(0).setDepth(120).setInteractive();
      this.add.text(x,y,label,{fontFamily:'sans-serif',fontSize:'17px',color:'#f1f3f6'}).setOrigin(0.5).setScrollFactor(0).setDepth(121);
      b.on('pointerdown',(p,a,e)=>{e.stopPropagation(); if(key==='interact'){this.handleInteract();return;} this.touch[key]=true;b.setAlpha(1);});
      const release=()=>{if(key in this.touch)this.touch[key]=false;b.setAlpha(0.72);};
      b.on('pointerup',release); b.on('pointerout',release); this.touchObjects.push(b);
    });
  }

  register(object, id) { this.interactables.push({ object, id }); }

  setStagePresentation() {
    const map = {
      chapter2Gate: ['CHAPTER 2 • THE FOREST THAT FOLLOWS', STORY.objectives.chapter2Gate],
      chapter2Forest: ['CHAPTER 2 • THE FOREST THAT FOLLOWS', STORY.objectives.chapter2Forest],
      chapter2Shrine: ['CHAPTER 2 • THE FOREST THAT FOLLOWS', STORY.objectives.chapter2Shrine],
      chapter3Mirror: ['CHAPTER 3 • THE MEMORY IN THE MIRROR', STORY.objectives.chapter3Mirror],
      chapter3Ruins: ['CHAPTER 3 • THE MEMORY IN THE MIRROR', STORY.objectives.chapter3Ruins],
      chapter4Ruins: ['CHAPTER 4 • THE OTHER YOU', STORY.objectives.chapter4Ruins],
      chapter4Truth: ['CHAPTER 4 • THE OTHER YOU', STORY.objectives.chapter4Truth],
      chapter4End: ['CHAPTER 4 • THE OTHER YOU', STORY.objectives.chapter4End],
      chapter4Done: ['CHAPTER 4 • THE OTHER YOU', 'The first four chapters are complete.']
    };
    const [chapter, objective] = map[this.save.stage] || map.chapter2Gate;
    this.chapterText.setText(chapter);
    this.objective.setText(`OBJECTIVE  •  ${objective}`);

    this.otherYou.setAlpha(this.save.stage === 'chapter4Truth' || this.save.stage === 'chapter4End' ? 1 : 0);
    this.returnBell.setAlpha(this.save.stage === 'chapter4End' ? 1 : 0.25);
  }

  showLine(line) {
    this.storyLock = true;
    this.dialogueBox.setVisible(true);
    this.speaker.setText(line.speaker || '').setVisible(Boolean(line.speaker));
    this.dialogueText.setText(line.text).setVisible(true);
    this.continueButton.setVisible(true);
    this.layoutUI();
  }

  hideDialogue() {
    this.dialogueBox.setVisible(false); this.speaker.setVisible(false);
    this.dialogueText.setVisible(false); this.continueButton.setVisible(false);
    this.storyLock = false;
  }

  startStory(lines, done) { this.dialogue.start(lines, done); }

  layoutUI() {
    const w=this.scale.width,h=this.scale.height, bw=Math.min(900,w-32);
    this.dialogueBox.setPosition(w/2,h-105).setSize(bw,Math.max(135,Math.min(175,h*.25)));
    this.speaker.setPosition(w/2-bw/2+24,h-145);
    this.dialogueText.setPosition(w/2,h-101);
    this.continueButton.setPosition(w/2,h-38);
    this.endCard.setPosition(w/2,h/2);
  }

  handleInteract() {
    if (this.dialogue.active || this.storyLock) { this.dialogue.advance(); return; }
    if (!this.currentInteractable) return;
    const id=this.currentInteractable.id;

    if (id==='oldWoman' && this.save.stage==='chapter2Gate') {
      this.startStory(STORY.chapter2Gate,()=>this.setStage('chapter2Forest'));
    } else if (id==='gate' && this.save.stage==='chapter2Forest') {
      this.startStory(STORY.chapter2Echo,()=>this.setStage('chapter2Shrine'));
    } else if (id==='shrine' && this.save.stage==='chapter2Shrine') {
      this.startStory(STORY.chapter2End,()=>this.setStage('chapter3Mirror'));
    } else if (id==='shrine' && this.save.stage==='chapter3Mirror') {
      this.startStory(STORY.chapter3Shrine,()=>this.startMirrorMemory());
    } else if (id==='fragment' && this.save.stage==='chapter3Ruins') {
      this.startStory(STORY.chapter3End,()=>this.setStage('chapter4Ruins'));
    } else if (id==='ruins' && this.save.stage==='chapter4Ruins') {
      this.startStory(STORY.chapter4Ruins,()=>this.setStage('chapter4Truth'));
    } else if (id==='otherYou' && this.save.stage==='chapter4Truth') {
      this.startStory(STORY.chapter4Truth,()=>this.setStage('chapter4End'));
    } else if (id==='bell' && this.save.stage==='chapter4End') {
      this.startStory(STORY.chapter4End,()=>this.finishChapter4());
    }
  }

  startMirrorMemory() {
    this.save.flags.mirrorSeen=true; saveGame(this.save);
    this.storyLock=true;
    this.startStory(STORY.chapter3Memory,()=>{
      this.save.flags.mirrorMemorySeen=true;
      this.setStage('chapter3Ruins');
    });
  }

  setStage(stage) {
    this.save.stage=stage;
    if(stage.startsWith('chapter3')) this.save.chapter=3;
    if(stage.startsWith('chapter4')) this.save.chapter=4;
    if(stage==='chapter2Forest'||stage==='chapter2Shrine') this.save.chapter=2;
    if(stage==='chapter2Gate') this.save.chapter=2;
    if(stage==='chapter4Done') this.save.flags.chapter4Complete=true;
    saveGame(this.save);
    this.setStagePresentation();
  }

  finishChapter4() {
    this.save.chapter=4;
    this.save.stage='chapter4Done';
    this.save.flags.chapter4Complete=true;
    saveGame(this.save);
    this.setStagePresentation();
    this.storyLock=true;
    this.endCard.setText('CHAPTER 4 COMPLETE\n\nThe bell stops.\n\nThe village remembers.\n\nTO BE CONTINUED…').setVisible(true);
  }

  update() {
    if(!this.player?.body)return;
    this.layoutUI();
    if(this.dialogue.active||this.storyLock){this.player.body.setVelocity(0);this.updatePrompt();return;}
    let x=0,y=0;
    if(this.keys.A.isDown||this.keys.LEFT.isDown||this.touch.left)x--;
    if(this.keys.D.isDown||this.keys.RIGHT.isDown||this.touch.right)x++;
    if(this.keys.W.isDown||this.keys.UP.isDown||this.touch.up)y--;
    if(this.keys.S.isDown||this.keys.DOWN.isDown||this.touch.down)y++;
    if(x||y){const v=new Phaser.Math.Vector2(x,y).normalize().scale(this.speed);this.player.body.setVelocity(v.x,v.y);}else this.player.body.setVelocity(0);
    this.updatePrompt();
  }

  updatePrompt() {
    let nearest=null,nd=Infinity;
    for(const item of this.interactables){
      if(!item.object.visible)continue;
      const x=item.object.x,y=item.object.y;
      const d=Phaser.Math.Distance.Between(this.player.x,this.player.y,x,y);
      if(d<125&&d<nd){nearest=item;nd=d;}
    }
    this.currentInteractable=nearest;
    if(!nearest){this.interact.setVisible(false);return;}
    this.interact.setText('E / TAP • Interact').setPosition(nearest.object.x,nearest.object.y-75).setVisible(true);
  }
}
