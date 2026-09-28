import { Chapter1World } from './phase11/Chapter1World.js';
import './style.css';

const game = document.getElementById('game');
const boot = document.getElementById('boot-message');
const errorBox = document.getElementById('boot-error');

if (game) {
  game.style.position = 'fixed';
  game.style.inset = '0';
  game.style.width = '100vw';
  game.style.height = '100vh';
}

const fail = (error) => {
  console.error('[YUGEN CHAPTER 1]', error);
  if (boot) boot.style.display = 'grid';
  if (errorBox) {
    errorBox.style.display = 'block';
    errorBox.textContent = String(error?.stack || error);
  }
};

try {
  const world = new Chapter1World(game);
  window.__yugenChapter1 = world;
  if (boot) boot.style.display = 'none';

  let running = true;
  const frame = () => {
    if (!running) return;
    world.update();
    world.render();
    requestAnimationFrame(frame);
  };
  requestAnimationFrame(frame);

  window.addEventListener('beforeunload', () => {
    running = false;
    world.destroy();
  }, { once: true });
} catch (error) {
  fail(error);
}
