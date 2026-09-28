export class MobileControls {
  constructor(container, { onInteract, onInventory, onMenu, onAction, onDialogueNext } = {}) {
    this.container = container;
    this.input = null;
    this.activePointer = null;
    this.onInteract = onInteract;
    this.onInventory = onInventory;
    this.onMenu = onMenu;
    this.onAction = onAction;
    this.onDialogueNext = onDialogueNext;

    this.root = document.createElement('div');
    this.root.className = 'mobile-controls';
    Object.assign(this.root.style, {
      position: 'fixed', inset: '0', pointerEvents: 'none', zIndex: '2147483647',
      display: 'none', touchAction: 'none', userSelect: 'none', WebkitUserSelect: 'none',
      width: '100vw', height: '100vh'
    });

    this.joystick = this.makeJoystick();
    this.interact = this.makeButton('Interact', 'mobile-interact');
    this.action = this.makeButton('Action', 'mobile-action');
    this.inventory = this.makeButton('Bag', 'mobile-inventory');
    this.menu = this.makeButton('Menu', 'mobile-menu');
    this.root.append(this.joystick, this.interact, this.action, this.inventory, this.menu);
    document.body.appendChild(this.root);

    this.interact.addEventListener('pointerdown', (e) => { e.preventDefault(); this.onInteract?.(); });
    this.action.addEventListener('pointerdown', (e) => { e.preventDefault(); this.onAction?.(); });
    this.inventory.addEventListener('pointerdown', (e) => { e.preventDefault(); this.onInventory?.(); });
    this.menu.addEventListener('pointerdown', (e) => { e.preventDefault(); this.onMenu?.(); });

    this.joystick.addEventListener('pointerdown', this.onPointerDown);
    this.joystick.addEventListener('pointermove', this.onPointerMove);
    this.joystick.addEventListener('pointerup', this.onPointerUp);
    this.joystick.addEventListener('pointercancel', this.onPointerUp);
    this.joystick.addEventListener('lostpointercapture', this.onPointerUp);

    this.onResize = () => this.updateLayout();
    window.addEventListener('resize', this.onResize, { passive: true });
    window.addEventListener('orientationchange', this.onResize, { passive: true });
    this.updateLayout();
  }

  attachInput(input) { this.input = input; }

  makeJoystick() {
    const base = document.createElement('div');
    base.className = 'mobile-joystick';
    Object.assign(base.style, {
      position: 'fixed', left: 'max(24px, env(safe-area-inset-left))', bottom: 'max(24px, env(safe-area-inset-bottom))',
      width: '124px', height: '124px', borderRadius: '50%', background: 'rgba(15,22,35,.82)',
      border: '3px solid rgba(255,255,255,.55)', boxShadow: '0 4px 18px rgba(0,0,0,.45)',
      pointerEvents: 'auto', touchAction: 'none', boxSizing: 'border-box'
    });
    this.stick = document.createElement('div');
    Object.assign(this.stick.style, {
      position: 'absolute', left: '50%', top: '50%', width: '58px', height: '58px', marginLeft: '-29px', marginTop: '-29px',
      borderRadius: '50%', background: 'rgba(235,242,255,.9)', border: '3px solid rgba(255,255,255,.95)',
      boxShadow: '0 2px 8px rgba(0,0,0,.4)', boxSizing: 'border-box'
    });
    base.appendChild(this.stick);
    return base;
  }

  makeButton(label, className) {
    const button = document.createElement('button');
    button.type = 'button';
    button.className = className;
    button.textContent = label;
    Object.assign(button.style, {
      position: 'fixed', width: '70px', height: '70px', borderRadius: '50%',
      border: '3px solid rgba(255,255,255,.55)', background: 'rgba(15,22,35,.86)', color: '#fff',
      fontSize: '13px', fontWeight: '700', pointerEvents: 'auto', touchAction: 'none',
      WebkitTapHighlightColor: 'transparent', boxShadow: '0 4px 18px rgba(0,0,0,.45)',
      padding: '0', zIndex: '2'
    });
    if (className === 'mobile-action') { button.style.right = 'max(24px, env(safe-area-inset-right))'; button.style.bottom = '118px'; }
    if (className === 'mobile-interact') { button.style.right = '110px'; button.style.bottom = 'max(32px, env(safe-area-inset-bottom))'; }
    if (className === 'mobile-inventory') { button.style.right = 'max(24px, env(safe-area-inset-right))'; button.style.bottom = 'max(32px, env(safe-area-inset-bottom))'; }
    if (className === 'mobile-menu') { button.style.right = '110px'; button.style.bottom = '126px'; }
    return button;
  }

  onPointerDown = (event) => {
    event.preventDefault();
    if (this.activePointer !== null) return;
    this.activePointer = event.pointerId;
    this.joystick.setPointerCapture?.(event.pointerId);
    this.updateVector(event.clientX, event.clientY);
  };

  onPointerMove = (event) => {
    if (event.pointerId !== this.activePointer) return;
    event.preventDefault();
    this.updateVector(event.clientX, event.clientY);
  };

  onPointerUp = (event) => {
    if (this.activePointer !== null && event.pointerId !== this.activePointer) return;
    this.activePointer = null;
    this.input?.setTouchVector(0, 0, false);
    this.stick.style.transform = 'translate(0px, 0px)';
  };

  updateVector(clientX, clientY) {
    const rect = this.joystick.getBoundingClientRect();
    const cx = rect.left + rect.width / 2;
    const cy = rect.top + rect.height / 2;
    let dx = clientX - cx;
    let dy = clientY - cy;
    const length = Math.hypot(dx, dy);
    const max = rect.width * 0.36;
    const scale = length > max ? max / length : 1;
    dx *= scale;
    dy *= scale;
    this.stick.style.transform = `translate(${dx}px, ${dy}px)`;
    this.input?.setTouchVector(dx / max, dy / max, true);
  }

  updateLayout() {
    const touchDevice = (navigator.maxTouchPoints || 0) > 0 || 'ontouchstart' in window;
    this.root.style.display = touchDevice ? 'block' : 'none';
  }

  setDialogueMode(active) {
    this.interact.textContent = active ? 'Next' : 'Interact';
    this.action.style.display = active ? 'none' : 'block';
    this.inventory.style.display = active ? 'none' : 'block';
    this.menu.style.display = active ? 'none' : 'block';
  }

  destroy() {
    this.input?.setTouchVector(0, 0, false);
    window.removeEventListener('resize', this.onResize);
    window.removeEventListener('orientationchange', this.onResize);
    this.root.remove();
  }
}
