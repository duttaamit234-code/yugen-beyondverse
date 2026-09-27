import { BOOT_CONFIG } from './BootConfig.js';

export class BootPipeline {
  constructor({ onProgress = () => {}, onComplete = () => {}, onError = () => {} } = {}) {
    this.onProgress = onProgress;
    this.onComplete = onComplete;
    this.onError = onError;
  }

  async start() {
    try {
      this.onProgress(0, 'Initializing engine…');
      await this.nextFrame();
      this.onProgress(50, `Preparing ${BOOT_CONFIG.gameName}…`);
      await this.nextFrame();
      this.onProgress(100, 'Boot complete');
      this.onComplete(BOOT_CONFIG);
      return BOOT_CONFIG;
    } catch (error) {
      this.onError(error);
      throw error;
    }
  }

  nextFrame() {
    return new Promise((resolve) => requestAnimationFrame(resolve));
  }
}
