export class UIManager {
  constructor(container) {
    this.container = container;
    this.layers = new Map();
    this.root = document.createElement('div');
    this.root.className = 'game-ui-root';
    this.root.style.position = 'absolute';
    this.root.style.inset = '0';
    this.root.style.pointerEvents = 'none';
    container.appendChild(this.root);
  }

  register(id, element) {
    element.dataset.uiId = id;
    this.layers.set(id, element);
    this.root.appendChild(element);
    return () => {
      this.layers.delete(id);
      element.remove();
    };
  }

  show(id) { const element = this.layers.get(id); if (element) element.hidden = false; }
  hide(id) { const element = this.layers.get(id); if (element) element.hidden = true; }
  get(id) { return this.layers.get(id) ?? null; }

  destroy() {
    this.layers.clear();
    this.root.remove();
  }
}
