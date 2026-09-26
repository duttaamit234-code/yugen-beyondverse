# Yugen: The World That Remembers

A story-driven 2D exploration game built with Phaser 4.

## First playable slice

The current goal is a deliberately small, testable vertical slice:

- Explore a compact village
- Move with WASD, arrow keys, and touch controls on small screens
- Collide with buildings and environmental landmarks
- Meet the Old Woman at the village gate
- Advance readable, speaker-aware dialogue
- Receive a clear objective
- Discover the first contradiction in the story
- Find the stone marker that becomes the next narrative lead

## Narrative principle

The game reveals its mystery through play rather than dumping lore into the player.

The core question is:

> Why does this world remember the protagonist differently from how the protagonist remembers themselves?

The first chapter should make the player curious before it makes the player knowledgeable.

## Development rule

Build one playable slice at a time:

1. Implement one mechanic or story beat.
2. Playtest it.
3. Fix confusion, friction, or boredom.
4. Only then expand the world or system.

This keeps the project small enough to iterate and leaves room for actual player feedback.

## Development

Install dependencies:

```bash
npm install
```

Run locally:

```bash
npm run dev
```

Build for production:

```bash
npm run build
```

The game remains separate from the existing Yugen web applications in this repository so it can later be packaged for Android with the same web build.
