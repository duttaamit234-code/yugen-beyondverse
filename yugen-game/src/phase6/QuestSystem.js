export class QuestSystem {
  constructor(definitions = {}) {
    this.definitions = definitions;
    this.active = new Map();
    this.completed = new Set();
    this.listeners = new Set();
  }

  onChange(listener) { this.listeners.add(listener); return () => this.listeners.delete(listener); }
  emit() { const state = this.getState(); for (const listener of this.listeners) listener(state); }

  start(id) {
    const definition = this.definitions[id];
    if (!definition || this.active.has(id) || this.completed.has(id)) return false;
    this.active.set(id, { id, objectiveIndex: 0, completed: false });
    this.emit();
    return true;
  }

  completeObjective(id, objectiveId) {
    const quest = this.active.get(id);
    const definition = this.definitions[id];
    if (!quest || !definition) return false;
    const index = definition.objectives.findIndex((objective) => objective.id === objectiveId);
    if (index < 0 || index > quest.objectiveIndex) return false;
    if (index < quest.objectiveIndex) return true;
    quest.objectiveIndex += 1;
    if (quest.objectiveIndex >= definition.objectives.length) {
      quest.completed = true;
      this.active.delete(id);
      this.completed.add(id);
    }
    this.emit();
    return true;
  }

  getState() {
    return [...this.active.values()].map((quest) => {
      const definition = this.definitions[quest.id];
      return {
        id: quest.id,
        title: definition.title,
        description: definition.description,
        currentObjective: definition.objectives[quest.objectiveIndex] ?? null,
        progress: `${quest.objectiveIndex}/${definition.objectives.length}`
      };
    });
  }
}
