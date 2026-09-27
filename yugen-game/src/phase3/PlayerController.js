import * as THREE from 'three';

export class PlayerController {
  constructor(player, input) {
    this.player = player;
    this.input = input;
    this.speed = 4.5;
    this.maxStep = 0.1;
    this.velocity = new THREE.Vector3();
  }

  update(delta) {
    const dt = Math.min(delta, 0.05);
    const input = this.input.getVector();
    const target = new THREE.Vector3(input.x, 0, input.z).multiplyScalar(this.speed);
    this.velocity.lerp(target, 1 - Math.exp(-14 * dt));
    const distance = Math.min(this.velocity.length() * dt, this.maxStep);
    if (distance > 0) {
      const direction = this.velocity.clone().normalize();
      this.player.position.addScaledVector(direction, distance);
      this.player.rotation.y = Math.atan2(direction.x, direction.z);
    }
    this.player.position.x = THREE.MathUtils.clamp(this.player.position.x, -14, 14);
    this.player.position.z = THREE.MathUtils.clamp(this.player.position.z, -10, 10);
  }
}
