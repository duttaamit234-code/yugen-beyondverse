import { questData } from '../phase6/QuestData.js';
import { QuestSystem } from '../phase6/QuestSystem.js';
import { UIManager } from '../phase7/UIManager.js';
import { QuestTrackerUI } from '../phase7/QuestTrackerUI.js';
import { itemData } from './ItemData.js';
import { InventorySystem } from './InventorySystem.js';
import { InventoryUI } from './InventoryUI.js';

export class SystemsHub {
  constructor(container) {
    this.ui = new UIManager(container);
    this.quests = new QuestSystem(questData);
    this.inventory = new InventorySystem(itemData);
    this.questUI = new QuestTrackerUI(this.ui, this.quests);
    this.inventoryUI = new InventoryUI(this.ui, this.inventory);
    this.handleKey = (event) => {
      if (event.key.toLowerCase() === 'i') this.inventoryUI.toggle();
    };
    window.addEventListener('keydown', this.handleKey);
  }

  destroy() {
    window.removeEventListener('keydown', this.handleKey);
    this.questUI.destroy();
    this.inventoryUI.destroy();
    this.ui.destroy();
  }
}
