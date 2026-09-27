export class InputController {
  constructor(target = window) {
    this.target = target;
    this.keys = new Set();
    this.touch = { x: 0, y: 0, active: false };
    this.enabled = true;
    this.onKeyDown = (event) => {
      if (!this.enabled) return;
      const key = event.key.toLowerCase();
      if (['w', 'a', 's', 'd', 'arrowup', 'arrowdown', 'arrowleft', 'arrowright'].includes(key)) {
        event.preventDefault();
        this.keys.add(key);
      }
    };
    this.onKeyUp = (event) => this.keys.delete(event.key.toLowerCase());
    target.addEventListener('keydown', this.onKeyDown);
    target.addEventListener('keyup', this.onKeyUp);
    target.addEventListener('blur', () => this.keys.clear());
  }

  setTouchVector(x, y, active = true) {
    this.touch = { x, y, active };
  }

  getVector() {
    if (!this.enabled) return { x: 0, y: 0 };
    let x = 0;
    let z = 0;
    if (this.keys.has('a') || this.keys.has('arrowleft')) x -= 1;
    if (this.keys.has('d') || this.keys.has('arrowright')) x += 1;
    if (this.keys.has('w') || this.keys.has('arrowup')) z -= 1;
    if (this.keys.has('s') || this.keys.has('arrowdown')) z += 1;
    if (x !== 0 || z !== 0) {
      const length = Math.hypot(x, z);
      return { x: x / length, z: z / length };
    }
    if (this.touch.active) return { x: this.touch.x, z: this.touch.y };
    return { x: 0, z: 0 };
  }

  destroy() {
    this.target.removeEventListener('keydown', this.onKeyDown);
    this.target.removeEventListener('keyup', this.onKeyUp);
  }
}
