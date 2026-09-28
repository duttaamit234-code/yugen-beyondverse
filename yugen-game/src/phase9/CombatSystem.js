export class CombatSystem {
  constructor() {
    this.entities = new Map();
    this.listeners = new Set();
  }
  register(id, entity) { this.entities.set(id, { ...entity, hp: entity.maxHp }); }
  onChange(listener) { this.listeners.add(listener); return () => this.listeners.delete(listener); }
  emit() { for (const listener of this.listeners) listener(this.getState()); }
  attack(attackerId, targetId) {
    const attacker = this.entities.get(attackerId);
    const target = this.entities.get(targetId);
    if (!attacker || !target || target.hp <= 0 || attacker.attack <= 0) return false;
    target.hp = Math.max(0, target.hp - attacker.attack);
    target.defeated = target.hp === 0;
    this.emit();
    return true;
  }
  heal(id, amount) {
    const entity = this.entities.get(id);
    if (!entity || entity.hp <= 0 || amount <= 0) return false;
    entity.hp = Math.min(entity.maxHp, entity.hp + amount);
    this.emit();
    return true;
  }
  getState() { return Object.fromEntries(this.entities); }
}
