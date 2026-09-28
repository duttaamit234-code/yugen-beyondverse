export class InventoryUI {
  constructor(uiManager, inventory) {
    this.inventory = inventory;
    this.root = document.createElement('section');
    this.root.className = 'inventory-panel';
    this.root.hidden = true;
    this.root.style.pointerEvents = 'auto';
    this.root.style.position = 'absolute';
    this.root.style.inset = '10% 10%';
    this.root.style.padding = '1rem';
    this.root.style.background = 'rgba(8,12,20,.94)';
    this.root.style.color = '#fff';
    uiManager.register('inventory', this.root);
    this.unsubscribe = inventory.onChange((items) => this.render(items));
    this.render(inventory.getState());
  }

  toggle() { this.root.hidden = !this.root.hidden; }

  render(items) {
    this.root.replaceChildren();
    const title = document.createElement('h2');
    title.textContent = 'Inventory';
    this.root.appendChild(title);
    if (!items.length) {
      const empty = document.createElement('p');
      empty.textContent = 'Inventory is empty.';
      this.root.appendChild(empty);
      return;
    }
    const list = document.createElement('div');
    list.style.display = 'grid';
    list.style.gridTemplateColumns = 'repeat(auto-fit,minmax(9rem,1fr))';
    list.style.gap = '0.6rem';
    for (const item of items) {
      const card = document.createElement('article');
      card.textContent = `${item.name} × ${item.quantity}`;
      card.title = item.description;
      card.style.padding = '0.6rem';
      card.style.border = '1px solid rgba(255,255,255,.18)';
      list.appendChild(card);
    }
    this.root.appendChild(list);
  }

  destroy() { this.unsubscribe?.(); this.root.remove(); }
}
