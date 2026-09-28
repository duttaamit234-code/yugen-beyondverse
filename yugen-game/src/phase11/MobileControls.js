export class MobileControls {
  constructor(container, { onInteract, onInventory, onMenu, onAction, onDialogueNext } = {}) {
    this.container = container;
    this.input = null;
    this.activePointer = null;
    this.center = { x: 0, y: 0 };
    this.radius = 58;
    this.onInteract = onInteract;
    this.onInventory = onInventory;
    this.onMenu = onMenu;
    this.onAction = onAction;
    this.onDialogueNext = onDialogueNext;

    this.root = document.createElement('div');
    this.root.className = 'mobile-controls';
    Object.assign(this.root.style, {
      position: 'absolute', inset: '0', pointerEvents: 'none', zIndex: '20',
      display: 'none', touchAction: 'none', userSelect: 'none', WebkitUserSelect: 'none'
    });

    this.joystick = this.makeJoystick();
    this.interact = this.makeButton('Interact', 'mobile-interact');
    this.action = this.makeButton('Action', 'mobile-action');
    this.inventory = this.makeButton('Bag', 'mobile-inventory');
    this.menu = this.makeButton('Menu', 'mobile-menu');
    this.root.append(this.joystick, this.interact, this.action, this.inventory, this.menu);
    container.appendChild(this.root);

    this.interact.addEventListener('pointerdown', (e) => { e.preventDefault(); this.onInteract?.(); });
    this.action.addEventListener('pointerdown', (e) => { e.preventDefault(); this.onAction?.(); });
    this.inventory.addEventListener('pointerdown', (e) => { e.preventDefault(); this.onInventory?.(); });
    this.menu.addEventListener('pointerdown', (e) => { e.preventDefault(); this.onMenu?.(); });

    this.joystick.addEventListener('pointerdown', this.onPointerDown);
    this.joystick.addEventListener('pointermove', this.onPointerMove);
    this.joystick.addEventListener('pointerup', this.onPointerUp);
    this.joystick.addEventListener('pointercancel', this.onPointerUp);
    this.updateVisibility();
    this.onResize = () => this.updateVisibility();
    window.addEventListener('resize', this.onResize);
  }

  attachInput(input) { this.input = input; }

  makeJoystick() {
    const base = document.createElement('div');
    base.className = 'mobile-joystick';
    Object.assign(base.style, {
      position: 'absolute', left: '24px', bottom: '24px', width: '116px', height: '116px',
      borderRadius: '50%', background: 'rgba(15,22,35,.68)', border: '2px solid rgba(255,255,255,.3)',
      pointerEvents: 'auto', touchAction: 'none', boxSizing: 'border-box'
    });
    this.stick = document.createElement('div');
    Object.assign(this.stick.style, {
      position: 'absolute', left: '50%', top: '50%', width: '54px', height: '54px', marginLeft: '-27px', marginTop: '-27px',
      borderRadius: '50%', background: 'rgba(220,230,245,.75)', border: '2px solid rgba(255,255,255,.75)', boxSizing: 'border-box'
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
      position: 'absolute', width: '64px', height: '64px', borderRadius: '50%',
      border: '2px solid rgba(255,255,255,.35)', background: 'rgba(15,22,35,.75)', color: '#fff',
      fontSize: '12px', fontWeight: '700', pointerEvents: 'auto', touchAction: 'none',
      WebkitTapHighlightColor: 'transparent'
    });
    if (className === 'mobile-action') { button.style.right = '26px'; button.style.bottom = '106px'; }
    if (className === 'mobile-interact') { button.style.right = '102px'; button.style.bottom = '46px'; }
    if (className === 'mobile-inventory') { button.style.right = '26px'; button.style.bottom = '32px'; }
    if (className === 'mobile-menu') { button.style.right = '102px'; button.style.bottom = '118px'; }
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
    if (event.pointerId !== this.activePointer) return;
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
    dx *= scale; dy *= scale;
    this.stick.style.transform = `translate(${dx}px, ${dy}px)`;
    this.input?.setTouchVector(dx / max, dy / max, true);
  }

  updateVisibility() {
    const touchDevice = window.matchMedia?.('(pointer: coarse)').matches || navigator.maxTouchPoints > 0;
    this.root.style.display = touchDevice ? 'block' : 'none';
  }

  setDialogueMode(active) {
    this.interact.textContent = active ? 'Next' : 'Interact';
    this.action.style.display = active ? 'none' : 'block';
    this.interact.onclick = active ? this.onDialogueNext : null;
  }

  destroy() {
    this.input?.setTouchVector(0, 0, false);
    window.removeEventListener('resize', this.onResize);
    this.root.remove();
  }
}
