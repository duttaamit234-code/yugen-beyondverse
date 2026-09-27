import { Phase2World } from './Phase2World.js';

export function startPhase2Test(container) {
  const world = new Phase2World(container);
  let frame = 0;
  let raf = 0;

  const loop = () => {
    if (world.disposed) return;
    world.update();
    world.render();
    frame = requestAnimationFrame(loop);
  };
  loop();

  return () => {
    cancelAnimationFrame(frame);
    world.destroy();
  };
}
