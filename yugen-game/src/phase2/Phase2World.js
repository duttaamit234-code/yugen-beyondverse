import * as THREE from 'three';

/**
 * Phase 2: small 3D test world.
 * Rendering is isolated from gameplay so later movement/collision systems can
 * consume the same world without rewriting the renderer.
 */
export class Phase2World {
  constructor(container) {
    this.container = container;
    this.scene = new THREE.Scene();
    this.scene.background = new THREE.Color(0x101827);

    this.camera = new THREE.PerspectiveCamera(45, 1, 0.1, 500);
    this.camera.position.set(10, 14, 10);

    this.renderer = new THREE.WebGLRenderer({ antialias: true, powerPreference: 'high-performance' });
    this.renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 1.5));
    this.renderer.shadowMap.enabled = false;
    this.renderer.outputColorSpace = THREE.SRGBColorSpace;
    container.appendChild(this.renderer.domElement);

    this.clock = new THREE.Clock();
    this.player = null;
    this.disposed = false;
    this.resizeObserver = new ResizeObserver(() => this.resize());
    this.resizeObserver.observe(container);

    this.buildLighting();
    this.buildMap();
    this.buildPlayer();
    this.resize();
  }

  buildLighting() {
    this.scene.add(new THREE.HemisphereLight(0xbfd7ff, 0x243021, 1.8));
    const sun = new THREE.DirectionalLight(0xfff0cf, 1.5);
    sun.position.set(8, 16, 5);
    this.scene.add(sun);
  }

  buildMap() {
    const ground = new THREE.Mesh(
      new THREE.PlaneGeometry(32, 24),
      new THREE.MeshLambertMaterial({ color: 0x34553b })
    );
    ground.rotation.x = -Math.PI / 2;
    this.scene.add(ground);

    const path = new THREE.Mesh(
      new THREE.PlaneGeometry(5, 24),
      new THREE.MeshLambertMaterial({ color: 0x77644d })
    );
    path.rotation.x = -Math.PI / 2;
    path.position.y = 0.012;
    this.scene.add(path);

    const crossPath = new THREE.Mesh(
      new THREE.PlaneGeometry(32, 4),
      new THREE.MeshLambertMaterial({ color: 0x77644d })
    );
    crossPath.rotation.x = -Math.PI / 2;
    crossPath.position.y = 0.014;
    this.scene.add(crossPath);

    const houseMaterial = new THREE.MeshLambertMaterial({ color: 0x79533f });
    const roofMaterial = new THREE.MeshLambertMaterial({ color: 0x44323b });
    [[-9,-6],[8,-6],[-9,7],[8,7]].forEach(([x,z]) => {
      const house = new THREE.Mesh(new THREE.BoxGeometry(4.5, 2.8, 3.2), houseMaterial);
      house.position.set(x, 1.4, z);
      this.scene.add(house);
      const roof = new THREE.Mesh(new THREE.ConeGeometry(3.1, 1.8, 4), roofMaterial);
      roof.rotation.y = Math.PI / 4;
      roof.position.set(x, 3.7, z);
      this.scene.add(roof);
    });

    const treeTrunk = new THREE.MeshLambertMaterial({ color: 0x52382a });
    const treeLeaves = new THREE.MeshLambertMaterial({ color: 0x21442d });
    [[-5,-8],[5,-8],[-6,8],[5,8],[-12,0],[12,0]].forEach(([x,z]) => {
      const trunk = new THREE.Mesh(new THREE.CylinderGeometry(.18,.25,1.4,8), treeTrunk);
      trunk.position.set(x,.7,z);
      this.scene.add(trunk);
      const crown = new THREE.Mesh(new THREE.SphereGeometry(1.15,10,8), treeLeaves);
      crown.position.set(x,1.9,z);
      this.scene.add(crown);
    });
  }

  buildPlayer() {
    const group = new THREE.Group();
    const body = new THREE.Mesh(
      new THREE.CapsuleGeometry(.45, .8, 4, 8),
      new THREE.MeshLambertMaterial({ color: 0xd7dbe8 })
    );
    body.position.y = 0.9;
    group.add(body);
    const head = new THREE.Mesh(
      new THREE.SphereGeometry(.32, 12, 8),
      new THREE.MeshLambertMaterial({ color: 0xe4b28e })
    );
    head.position.y = 1.75;
    group.add(head);
    group.position.set(0, 0, 0);
    this.player = group;
    this.scene.add(group);
  }

  resize() {
    if (!this.container || this.disposed) return;
    const width = Math.max(1, this.container.clientWidth);
    const height = Math.max(1, this.container.clientHeight);
    this.camera.aspect = width / height;
    this.camera.updateProjectionMatrix();
    this.renderer.setSize(width, height, false);
  }

  update() {
    if (this.disposed) return;
    const target = this.player.position.clone();
    target.y = 0;
    const desired = target.clone().add(new THREE.Vector3(10, 14, 10));
    this.camera.position.lerp(desired, 0.08);
    this.camera.lookAt(target);
  }

  render() {
    this.renderer.render(this.scene, this.camera);
  }

  destroy() {
    this.disposed = true;
    this.resizeObserver.disconnect();
    this.renderer.dispose();
    this.renderer.domElement.remove();
  }
}
