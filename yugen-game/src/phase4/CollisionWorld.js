import * as THREE from 'three';

/**
 * Lightweight static collision world for the RPG prototype.
 * Gameplay collision is represented as 2D X/Z rectangles so it stays cheap
 * on mobile and remains independent from rendering meshes.
 */
export class CollisionWorld {
  constructor(bounds = { minX: -15.5, maxX: 15.5, minZ: -11.5, maxZ: 11.5 }) {
    this.bounds = bounds;
    this.obstacles = [];
  }

  addBox({ minX, maxX, minZ, maxZ, padding = 0.45 }) {
    this.obstacles.push({ minX, maxX, minZ, maxZ, padding });
  }

  resolve(position, radius = 0.45) {
    const next = position.clone();
    next.x = THREE.MathUtils.clamp(next.x, this.bounds.minX + radius, this.bounds.maxX - radius);
    next.z = THREE.MathUtils.clamp(next.z, this.bounds.minZ + radius, this.bounds.maxZ - radius);

    for (const obstacle of this.obstacles) {
      const minX = obstacle.minX - radius - obstacle.padding;
      const maxX = obstacle.maxX + radius + obstacle.padding;
      const minZ = obstacle.minZ - radius - obstacle.padding;
      const maxZ = obstacle.maxZ + radius + obstacle.padding;

      if (next.x <= minX || next.x >= maxX || next.z <= minZ || next.z >= maxZ) continue;

      const pushLeft = next.x - minX;
      const pushRight = maxX - next.x;
      const pushTop = next.z - minZ;
      const pushBottom = maxZ - next.z;
      const smallest = Math.min(pushLeft, pushRight, pushTop, pushBottom);

      if (smallest === pushLeft) next.x = minX;
      else if (smallest === pushRight) next.x = maxX;
      else if (smallest === pushTop) next.z = minZ;
      else next.z = maxZ;
    }

    return next;
  }
}
