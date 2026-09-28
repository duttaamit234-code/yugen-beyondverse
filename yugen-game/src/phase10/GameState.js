export function createGameState({ player = {}, quests = [], inventory = [] } = {}) {
  return {
    version: 1,
    player: { ...player },
    quests: [...quests],
    inventory: [...inventory]
  };
}
