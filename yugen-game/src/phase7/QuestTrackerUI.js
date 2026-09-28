export class QuestTrackerUI {
  constructor(uiManager, questSystem) {
    this.root = document.createElement('aside');
    this.root.className = 'quest-tracker';
    this.root.style.pointerEvents = 'auto';
    this.root.style.position = 'absolute';
    this.root.style.top = '1rem';
    this.root.style.left = '1rem';
    this.root.style.maxWidth = '22rem';
    this.root.style.padding = '0.8rem';
    this.root.style.background = 'rgba(10,15,25,.85)';
    this.root.style.color = '#fff';
    this.root.hidden = true;
    uiManager.register('questTracker', this.root);
    this.unsubscribe = questSystem.onChange((quests) => this.render(quests));
  }

  render(quests) {
    this.root.replaceChildren();
    if (!quests.length) { this.root.hidden = true; return; }
    this.root.hidden = false;
    for (const quest of quests) {
      const title = document.createElement('strong');
      title.textContent = quest.title;
      const objective = document.createElement('div');
      objective.textContent = quest.currentObjective?.text ?? 'Complete';
      const progress = document.createElement('small');
      progress.textContent = quest.progress;
      this.root.append(title, objective, progress);
    }
  }

  destroy() { this.unsubscribe?.(); this.root.remove(); }
}
