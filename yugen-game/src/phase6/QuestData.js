export const questData = {
  eastern_road: {
    id: 'eastern_road',
    title: 'The Eastern Road',
    description: 'Learn why the eastern road has been closed.',
    objectives: [
      { id: 'speak_guard', text: 'Speak with the village guard', type: 'interaction', target: 'village_guard' },
      { id: 'inspect_marker', text: 'Inspect the eastern road marker', type: 'interaction', target: 'road_marker' }
    ],
    reward: { xp: 25, items: [{ id: 'herb', quantity: 2 }] }
  }
};
