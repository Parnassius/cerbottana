import utils

async def leaderboard(self, room, user, arg):
  # pylint: disable=too-many-locals,too-many-statements
  if room is not None and not utils.is_voice(user):
    return

  body = utils.database_request(self, 'getleaderboard', {})
  if body:
    html = '<div style="max-height: 250px; overflow-y: auto">'
    html += '  <div style="text-align: center"><b><big>{titolo}</big></b></div>'
    html += '  <hr style="margin-bottom: 0">'
    html += '  <table style="width: 100%">'
    html += '    <thead>'
    html += '      <tr style="text-align: left">'
    html += '        <th>#</th>'
    html += '        <th>Utente</th>'
    html += '        <th style="text-align: center">Punteggio</th>'
    html += '      </tr>'
    html += '    </thead>'
    html += '    <tbody>'
    html += '      {tbody}'
    html += '    </tbody>'
    html += '  </table>'
    html += '</div>'

    titolo = '{} {} - Fase 1'.format(body[0]['descrizione'].replace('<', '&lt;'),
                                     body[0]['anno'])

    pos = 0
    ties = 0
    punteggio_prev = 0
    tbody = ''
    trow = '<tr>'
    trow += '  <td colspan="3">'
    trow += '    <hr style="margin:0">'
    trow += '  </td>'
    trow += '</tr>'
    trow += '<tr{opacity}>'
    trow += '  <td>{pos}</td>'
    trow += '  <td>{utente}</td>'
    trow += '  <td style="text-align: center">{punteggio}</td>'
    trow += '</tr>'
    for i in body:
      if pos == 0 or int(i['punteggio']) < punteggio_prev:
        pos += ties + 1
        ties = 0
      else:
        ties += 1

      if pos > 8:
        opacity = ' style="opacity: .5"'
      else:
        opacity = ''

      utente = i['utente'].replace('<', '&lt;')
      punteggio = i['punteggio']

      tbody += trow.format(opacity=opacity, pos=pos, utente=utente, punteggio=punteggio)

      punteggio_prev = int(i['punteggio'])

    await self.send_htmlbox(room, user, html.format(titolo=titolo, tbody=tbody))

  else:
    await self.send_reply(room, user, 'Nessun risultato trovato')


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
