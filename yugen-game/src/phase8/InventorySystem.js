export class InventorySystem {
  constructor(definitions = {}, capacity = 24) {
    this.definitions = definitions;
    this.capacity = capacity;
    this.items = new Map();
    this.listeners = new Set();
  }

  onChange(listener) { this.listeners.add(listener); return () => this.listeners.delete(listener); }
  emit() { for (const listener of this.listeners) listener(this.getState()); }

  add(id, quantity = 1) {
    const definition = this.definitions[id];
    if (!definition || quantity <= 0) return false;
    const current = this.items.get(id) ?? 0;
    if (!definition.stackable && current > 0) return false;
    const next = current + quantity;
    if (definition.stackable && next > definition.maxStack) return false;
    if (current === 0 && this.items.size >= this.capacity) return false;
    this.items.set(id, next);
    this.emit();
    return true;
  }

  remove(id, quantity = 1) {
    const current = this.items.get(id) ?? 0;
    if (quantity <= 0 || current < quantity) return false;
    const next = current - quantity;
    if (next === 0) this.items.delete(id);
    else this.items.set(id, next);
    this.emit();
    return true;
  }

  has(id, quantity = 1) { return (this.items.get(id) ?? 0) >= quantity; }

  getState() {
    return [...this.items.entries()].map(([id, quantity]) => ({ id, quantity, ...this.definitions[id] }));
  }
}
