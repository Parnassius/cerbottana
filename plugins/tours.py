import utils

import database


async def randpoketour(self, room, user, arg):
  if room is None or not utils.is_driver(user):
    return

  if arg.strip() == '':
    return await self.send_message(room, 'Inserisci almeno un Pokémon')

  megas = ['abomasnow', 'absol', 'aerodactyl', 'aggron', 'alakazam', 'altaria', 'ampharos',
           'audino', 'banette', 'beedrill', 'blastoise', 'blaziken', 'camerupt', 'diancie',
           'gallade', 'garchomp', 'gardevoir', 'gengar', 'glalie', 'gyarados', 'heracross',
           'houndoom', 'kangaskhan', 'latias', 'latios', 'lopunny', 'lucario', 'manectric',
           'mawile', 'medicham', 'metagross', 'pidgeot', 'pinsir', 'rayquaza', 'sableye',
           'salamence', 'sceptile', 'scizor', 'sharpedo', 'slowbro', 'steelix', 'swampert',
           'tyranitar', 'venusaur']
  megas_xy = ['charizard', 'mewtwo']
  megastones = ['Abomasite', 'Absolite', 'Aerodactylite', 'Aggronite', 'Alakazite', 'Altarianite',
                'Ampharosite', 'Audinite', 'Banettite', 'Beedrillite', 'Blastoisinite',
                'Blazikenite', 'Cameruptite', 'Charizardite X', 'Charizardite Y', 'Crucibellite',
                'Diancite', 'Galladite', 'Garchompite', 'Gardevoirite', 'Gengarite', 'Glalitite',
                'Gyaradosite', 'Heracronite', 'Houndoominite', 'Kangaskhanite', 'Latiasite',
                'Latiosite', 'Lopunnite', 'Lucarionite', 'Manectite', 'Mawilite', 'Medichamite',
                'Metagrossite', 'Mewtwonite X', 'Mewtwonite Y', 'Pidgeotite', 'Pinsirite',
                'Sablenite', 'Salamencite', 'Sceptilite', 'Scizorite', 'Sharpedonite',
                'Slowbronite', 'Steelixite', 'Swampertite', 'Tyranitarite', 'Venusaurite']

  bans = ['OU', 'UUBL', 'UU', 'RUBL', 'RU', 'NUBL', 'NU', 'PUBL', 'PU', 'ZU', 'NFE', 'LC Uber', 'LC']
  unbans = []
  if ',' in arg:
    sep = ','
  else:
    sep = ' '
  allow_megas = True
  for item in arg.split(sep):
    if utils.to_user_id(item) in ['nomega', 'nomegas']:
      allow_megas = False
      continue
    unbans.append(item.strip() + '-base')

  if allow_megas:
    for item in arg.split(sep):
      if utils.to_user_id(item) in megas:
        unbans.append(item.strip() + '-Mega-base')
      if utils.to_user_id(item) in megas_xy:
        unbans.append(item.strip() + '-Mega-X-base')
        unbans.append(item.strip() + '-Mega-Y-base')
  else:
    bans.extend(megastones)

  await self.send_message(room, '/tour new ou, elimination')
  await self.send_message(room, '/tour name !RANDPOKE TOUR' + ('' if allow_megas else ' (no mega)'))
  await self.send_message(room, '/tour autostart 12')
  await self.send_message(room, '/tour autodq 1.5')
  await self.send_message(room, '/tour scouting off')
  await self.send_message(room, '/tour rules {},{}'.format(','.join(['-' + i for i in bans]),
                                                          ','.join(['+' + i for i in unbans])))


commands = {'randpoketour': randpoketour}
