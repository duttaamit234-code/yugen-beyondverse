export class DialogueUI {
  constructor(container, dialogueSystem) {
    this.container = container;
    this.system = dialogueSystem;
    this.root = document.createElement('section');
    this.root.className = 'dialogue-panel';
    this.root.setAttribute('aria-live', 'polite');
    this.root.hidden = true;

    this.speaker = document.createElement('div');
    this.speaker.className = 'dialogue-speaker';
    this.text = document.createElement('div');
    this.text.className = 'dialogue-text';
    this.next = document.createElement('button');
    this.next.type = 'button';
    this.next.className = 'dialogue-next';
    this.next.textContent = 'Continue';

    this.root.append(this.speaker, this.text, this.next);
    container.appendChild(this.root);

    this.next.addEventListener('click', () => this.system.advance());
    this.unsubscribe = this.system.onChange((state) => this.render(state));
  }

  render(state) {
    this.root.hidden = !state.active;
    if (!state.active) return;
    this.speaker.textContent = state.speaker;
    this.text.textContent = state.text;
    this.next.textContent = state.index + 1 >= state.total ? 'Close' : 'Continue';
  }

  destroy() {
    this.unsubscribe?.();
    this.root.remove();
  }
}
