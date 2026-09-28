export class Chapter1Flow {
  constructor({ quests, dialogue, inventory, chapterData }) {
    this.quests = quests;
    this.dialogue = dialogue;
    this.inventory = inventory;
    this.chapterData = chapterData;
    this.started = false;
    this.completed = false;
  }

  start() {
    if (this.started) return;
    this.started = true;
    this.quests.start(this.chapterData.startingQuest);
  }

  onInteraction(targetId) {
    const activeQuest = this.quests.getState()[0];
    if (!activeQuest) return;
    const objective = activeQuest.currentObjective;
    if (objective?.target !== targetId) return;
    this.quests.completeObjective(activeQuest.id, objective.id);
  }

  update() {
    if (!this.started || this.completed) return;
    if (this.quests.completed?.has?.(this.chapterData.startingQuest)) {
      this.completed = true;
    }
  }

  getState() {
    return { id: this.chapterData.id, title: this.chapterData.title, started: this.started, completed: this.completed };
  }
}
