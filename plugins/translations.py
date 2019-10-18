import json

import utils

async def trad(self, room, user, arg):
  if room is not None and not utils.is_voice(user):
    return

  parola = utils.to_user_id(utils.remove_accents(arg.lower()))
  if parola == '':
    await self.send_reply(room, user, 'Cosa devo tradurre?')
    return

  results = []

  for i in TRANSLATIONS:
    for j in TRANSLATIONS[i]:
      if utils.to_user_id(utils.remove_accents(j['en'].lower())) == parola:
        results.append({'trad': j['it'],
                        'cat': i})
      elif utils.to_user_id(utils.remove_accents(j['it'].lower())) == parola:
        results.append({'trad': j['en'],
                        'cat': i})

  if results:
    if len(results) == 1:
      await self.send_reply(room, user, results[0]['trad'])
      return
    resultstext = ''
    for i in results:
      if resultstext != '':
        resultstext += ', '
      resultstext += '{trad} ({cat})'.format(trad=i['trad'], cat=i['cat'])
    print(resultstext)
    await self.send_reply(room, user, resultstext)
    return

  await self.send_reply(room, user, 'Non trovato')


with open('./data/translations.json', 'r') as f:
  TRANSLATIONS = json.load(f)


commands = {'trad': trad}
