import { Phase3World } from './Phase3World.js';

export function startPhase3Test(container) {
  const world = new Phase3World(container);
  let frame = 0;
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
