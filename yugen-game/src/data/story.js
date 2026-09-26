export const STORY = {
  title: 'YUGEN: THE WORLD THAT REMEMBERS',

  opening: [
    { speaker: '', text: 'You wake beneath an unfamiliar sky.' },
    { speaker: '', text: 'The village ahead is quiet. Too quiet.' },
    { speaker: '', text: 'A voice whispers your name from the empty road.' },
    { speaker: '', text: 'You turn. Nobody is there.' },
    { speaker: '???', text: '“You came back.”' },
    { speaker: 'You', text: '“I have never been here.”' },
    { speaker: '???', text: 'The old woman studies you for a moment, then looks away.' }
  ],

  oldWomanFirst: [
    { speaker: 'Old Woman', text: '“I remember you.”' },
    { speaker: 'You', text: '“That is impossible.”' },
    { speaker: 'Old Woman', text: '“Perhaps. But that has never stopped this village from remembering.”' },
    { speaker: 'Old Woman', text: '“Go to the stone marker north of the square. Do not touch it.”' },
    { speaker: 'You', text: '“Why?”' },
    { speaker: 'Old Woman', text: '“Because last time, you did.”' }
  ],

  stone: [
    { speaker: '', text: 'The stone is colder than the evening air.' },
    { speaker: '', text: 'For a moment, the village disappears.' },
    { speaker: '', text: 'You see the same road. The same houses. But the sky is red.' },
    { speaker: 'Unknown Voice', text: '“You said you would remember this time.”' },
    { speaker: '', text: 'Someone who looks exactly like you stands beside the stone.' },
    { speaker: 'You', text: '“That was me…”' },
    { speaker: '', text: 'The memory breaks before you can see their face clearly.' }
  ],

  missingHouse: [
    { speaker: 'Villager', text: '“There was a house here once.”' },
    { speaker: 'You', text: '“Who lived there?”' },
    { speaker: 'Villager', text: '“I… don’t think we should talk about that.”' },
    { speaker: '', text: 'Something catches the light beneath a loose floorboard.' },
    { speaker: '', text: 'You find an old photograph.' },
    { speaker: '', text: 'The village is in the picture. So are the villagers.' },
    { speaker: 'You', text: '“Why am I standing in this?”' },
    { speaker: '', text: 'The photograph is dated seventeen years ago.' }
  ],

  worldShift: [
    { speaker: '', text: 'You return to the village square.' },
    { speaker: '', text: 'Something is wrong.' },
    { speaker: '', text: 'A path that led toward the forest now bends somewhere else.' },
    { speaker: '', text: 'One of the houses has a different door.' },
    { speaker: '', text: 'A tree beside the road is gone.' },
    { speaker: 'Villager', text: '“Have we met before?”' },
    { speaker: 'You', text: '“You spoke to me this morning.”' },
    { speaker: 'Villager', text: '“I don’t remember that.”' }
  ],

  oldWomanSecond: [
    { speaker: 'You', text: '“What is happening to this place?”' },
    { speaker: 'Old Woman', text: '“Now you understand why I was afraid when I saw you.”' },
    { speaker: 'You', text: '“Tell me the truth.”' },
    { speaker: 'Old Woman', text: '“This is not the first time you have arrived here.”' },
    { speaker: 'You', text: '“How many times?”' },
    { speaker: 'Old Woman', text: '“I stopped counting after the village stopped changing in the same way twice.”' },
    { speaker: 'Old Woman', text: '“Find the place where you first disappeared.”' }
  ],

  objectives: {
    meetOldWoman: 'Speak with the Old Woman at the village gate.',
    stone: 'Investigate the stone marker north of the village square.',
    photograph: 'Find out what happened to the missing house.',
    worldShift: 'Return to the village square.',
    final: 'Find the place where you first disappeared.'
  }
};
