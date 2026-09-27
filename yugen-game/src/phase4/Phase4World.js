import * as THREE from 'three';
import { InputController } from '../phase3/InputController.js';
import { PlayerController } from '../phase3/PlayerController.js';
import { CollisionWorld } from './CollisionWorld.js';
import { InteractionSystem } from './InteractionSystem.js';

export class Phase4World {
  constructor(container) {
    this.container = container;
    this.scene = new THREE.Scene();
    this.scene.background = new THREE.Color(0x101827);
    this.camera = new THREE.PerspectiveCamera(45, 1, 0.1, 500);
    this.renderer = new THREE.WebGLRenderer({ antialias: true, powerPreference: 'high-performance' });
    this.renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 1.5));
    this.renderer.outputColorSpace = THREE.SRGBColorSpace;
    container.appendChild(this.renderer.domElement);

    this.clock = new THREE.Clock();
    this.disposed = false;
    this.input = new InputController(window);
    this.collision = new CollisionWorld();
    this.resizeObserver = new ResizeObserver(() => this.resize());
    this.resizeObserver.observe(container);

    this.buildLighting();
    this.buildMap();
    this.buildPlayer();
    this.buildInteractionTarget();
    this.resize();
  }

  buildLighting() {
    this.scene.add(new THREE.HemisphereLight(0xbfd7ff, 0x243021, 1.8));
    const sun = new THREE.DirectionalLight(0xfff0cf, 1.5);
    sun.position.set(8, 16, 5);
    this.scene.add(sun);
  }

  buildMap() {
    const ground = new THREE.Mesh(new THREE.PlaneGeometry(32, 24), new THREE.MeshLambertMaterial({ color: 0x34553b }));
    ground.rotation.x = -Math.PI / 2;
    this.scene.add(ground);

    const path = new THREE.Mesh(new THREE.PlaneGeometry(5, 24), new THREE.MeshLambertMaterial({ color: 0x77644d }));
    path.rotation.x = -Math.PI / 2;
    path.position.y = 0.012;
    this.scene.add(path);

    const cross = new THREE.Mesh(new THREE.PlaneGeometry(32, 4), new THREE.MeshLambertMaterial({ color: 0x77644d }));
    cross.rotation.x = -Math.PI / 2;
    cross.position.y = 0.014;
    this.scene.add(cross);

    const houseMaterial = new THREE.MeshLambertMaterial({ color: 0x79533f });
    const roofMaterial = new THREE.MeshLambertMaterial({ color: 0x44323b });
    [[-9, -6], [8, -6], [-9, 7], [8, 7]].forEach(([x, z]) => {
      const house = new THREE.Mesh(new THREE.BoxGeometry(4.5, 2.8, 3.2), houseMaterial);
      house.position.set(x, 1.4, z);
      this.scene.add(house);
      this.collision.addBox({ minX: x - 2.25, maxX: x + 2.25, minZ: z - 1.6, maxZ: z + 1.6 });

      const roof = new THREE.Mesh(new THREE.ConeGeometry(3.1, 1.8, 4), roofMaterial);
      roof.rotation.y = Math.PI / 4;
      roof.position.set(x, 3.7, z);
      this.scene.add(roof);
    });
  }

  buildPlayer() {
    const group = new THREE.Group();
    const body = new THREE.Mesh(new THREE.CapsuleGeometry(.45, .8, 4, 8), new THREE.MeshLambertMaterial({ color: 0xd7dbe8 }));
    body.position.y = 0.9;
    group.add(body);
    const head = new THREE.Mesh(new THREE.SphereGeometry(.32, 12, 8), new THREE.MeshLambertMaterial({ color: 0xe4b28e }));
    head.position.y = 1.75;
    group.add(head);
    this.player = group;
    this.scene.add(group);
    this.playerController = new PlayerController(group, this.input);

    const originalUpdate = this.playerController.update.bind(this.playerController);
    this.playerController.update = (delta) => {
      originalUpdate(delta);
      const resolved = this.collision.resolve(this.player.position, 0.45);
      this.player.position.copy(resolved);
    };
  }

  buildInteractionTarget() {
    const marker = new THREE.Mesh(
      new THREE.CylinderGeometry(0.5, 0.5, 1.2, 12),
      new THREE.MeshLambertMaterial({ color: 0xd6a84f })
    );
    marker.position.set(0, 0.6, -5);
    this.scene.add(marker);

    this.interactions = new InteractionSystem(this.player);
    this.interactions.register({
      position: marker.position,
      interact: () => {
        marker.scale.y = marker.scale.y === 1 ? 1.35 : 1;
      }
    });

    window.addEventListener('keydown', this.handleInteract = (event) => {
      if (event.key.toLowerCase() === 'e') this.interactions.interact();
    });
  }

  resize() {
    const width = Math.max(1, this.container.clientWidth);
    const height = Math.max(1, this.container.clientHeight);
    this.camera.aspect = width / height;
    this.camera.updateProjectionMatrix();
    this.renderer.setSize(width, height, false);
  }

  update() {
    if (this.disposed) return;
    const delta = this.clock.getDelta();
    this.playerController.update(delta);
    this.interactions.update();
    const target = this.player.position.clone();
    target.y = 0;
    const desired = target.clone().add(new THREE.Vector3(8, 12, 8));
    this.camera.position.lerp(desired, 1 - Math.exp(-7 * delta));
    this.camera.lookAt(target);
  }

  render() {
    this.renderer.render(this.scene, this.camera);
  }

  destroy() {
    this.disposed = true;
    this.resizeObserver.disconnect();
    this.input.destroy();
    window.removeEventListener('keydown', this.handleInteract);
    this.renderer.dispose();
    this.renderer.domElement.remove();
  }
}
