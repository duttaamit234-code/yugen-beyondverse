export class SceneManager {
  constructor() {
    this.current = null;
  }

  switchTo(scene) {
    if (this.current?.destroy) this.current.destroy();
    this.current = scene;
    this.current?.create?.();
  }

  update(delta) {
    this.current?.update?.(delta);
  }
}
