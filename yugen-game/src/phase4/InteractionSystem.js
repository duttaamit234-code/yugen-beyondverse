export class InteractionSystem {
  constructor(player, range = 1.8) {
    this.player = player;
    this.range = range;
    this.targets = [];
    this.activeTarget = null;
  }

  register(target) {
    if (!target?.position || typeof target.interact !== 'function') return () => {};
    this.targets.push(target);
    return () => {
      const index = this.targets.indexOf(target);
      if (index >= 0) this.targets.splice(index, 1);
    };
  }

  update() {
    let nearest = null;
    let nearestDistance = this.range;
    for (const target of this.targets) {
      const distance = this.player.position.distanceTo(target.position);
      if (distance <= nearestDistance) {
        nearest = target;
        nearestDistance = distance;
      }
    }
    this.activeTarget = nearest;
    return nearest;
  }

  interact() {
    this.update();
    if (!this.activeTarget) return false;
    this.activeTarget.interact();
    return true;
  }
}
