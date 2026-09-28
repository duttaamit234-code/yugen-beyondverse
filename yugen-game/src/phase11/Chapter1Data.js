export const chapter1Data = {
  id: 'chapter1',
  title: 'The Road Before Sunset',
  startingQuest: 'eastern_road',
  spawn: { x: 0, y: 0, z: 6 },
  npcs: [
    { id: 'village_guard', name: 'Village Guard', position: { x: 0, y: 0, z: -5 }, dialogueId: 'village_guard_intro' },
    { id: 'quartermaster', name: 'Quartermaster', position: { x: 7, y: 0, z: 2 }, dialogueId: 'placeholder_intro' }
  ],
  locations: [
    { id: 'village_square', name: 'Village Square', position: { x: 0, y: 0, z: 0 } },
    { id: 'eastern_road', name: 'Eastern Road', position: { x: 0, y: 0, z: -10 } }
  ]
};
