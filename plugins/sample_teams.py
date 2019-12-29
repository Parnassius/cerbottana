import math

import utils

async def sample_teams(self, room, user, arg):
  if room is None or not utils.is_voice(user):
    return

  format = arg

  aliases = {'ag': 'anythinggoes',
             'uber': 'ubers',
             'dou': 'doublesou',
             'bh': 'balancedhackmons'}

  if format in aliases:
    format = aliases[format]

  if format[:3] != 'gen':
    format = 'gen8' + format

  if format in utils.SAMPLE_TEAMS:
    picon = '<span class="picon" style="background: transparent url(&quot;//play.pokemonshowdown.com/sprites/pokemonicons-sheet.png?g8&quot;) no-repeat scroll -{left}px -{top}px"></span>'

    html = '<details>'
    html += '  <summary><b><big>Sample teams</big></b></summary>'
    first = True
    for i in utils.SAMPLE_TEAMS[format]:
      if not first:
        html += '<hr>'
      first = False
      for num in utils.SAMPLE_TEAMS[format][i]['icons']:
        left = (num % 12) * 40
        top = math.floor(num / 12) * 30
        html += picon.format(left=left, top=top)
      html += '<details>'
      html += '  <summary>' + i + '</summary>'
      html += '  <pre class="textbox" style="margin-top: 0">' + utils.SAMPLE_TEAMS[format][i]['importable'] + '</pre>'
      html += '</details>'
    html += '</details>'
    await self.send_htmlbox(room, None, html)


commands = {'sample': sample_teams,
            'samples': sample_teams,
            'sampleteams': sample_teams}
