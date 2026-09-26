export default class DialogueSystem {
  constructor(scene) {
    this.scene = scene;
    this.queue = [];
    this.active = false;
    this.onEnd = null;
  }

  start(lines, onEnd = null) {
    this.queue = [...lines];
    this.active = true;
    this.onEnd = onEnd;
    this.advance();
  }

  advance() {
    if (!this.active) return;

    if (this.queue.length === 0) {
      this.end();
      return;
    }

    const line = this.queue.shift();
    if (typeof this.scene.showDialogueLine === 'function') {
      this.scene.showDialogueLine(line);
    } else {
      this.scene.showLine(line);
    }
  }

  end() {
    this.active = false;
    this.scene.hideDialogue();

    const callback = this.onEnd;
    this.onEnd = null;
    if (callback) callback();
  }
}
