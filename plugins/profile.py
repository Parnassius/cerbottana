import utils

async def champion(self, room, user, arg):
  await elitefour(self, room, user, 'ou')

async def elitefour(self, room, user, arg):
  if room is not None and not utils.is_voice(user):
    return

  body = utils.database_request(self,
                                'getelitefour',
                                {'tier': utils.to_user_id(arg)})
  if body:
    if len(body) == 1:
      if room is not None and utils.is_voice(user):
        await profile(self, room, user, body[0]['utente'])
      else:
        await self.send_pm(user, body[0]['utente'])
    elif len(body) > 1:
      if room is None:
        text = ''
        for i in body:
          if text != '':
            text += ' - '
          text += '{tier}: {utente}'.format(tier=i['tier'], utente=i['utente'])
        await self.send_reply(room, user, text)
        return
      html = '<table>'
      html += '  <tr>'
      html += '    <td style="text-align: center; padding: 5px 0 10px">'
      html += '      <b><big>Lega Pokémon</big></b>'
      html += '    </td>'
      html += '  </tr>'
      first = True
      for i in body:
        utente = i['utente']
        html += '  <tr>'
        html += '    <td>'
        if utente is None:
          color = 'inherit'
        else:
          color = utils.username_color(utils.to_user_id(utente))
        html += '{tier}: <b style="color: {color}">{utente}</b><br>'.format(tier=i['tier'],
                                                                            color=color,
                                                                            utente=utente)
        html += '    </td>'
        html += '  </tr>'
        if first:
          html += '  <tr>'
          html += '    <td colspan="3">'
          html += '      <hr style="margin:0">'
          html += '    </td>'
          html += '  </tr>'
          first = False
      html += '</table>'
      await self.send_htmlbox(room, html)

async def profile(self, room, user, arg):
  # pylint: disable=too-many-locals
  if room is None or not utils.is_voice(user):
    return

  if arg.strip() == '':
    arg = user

  arg = utils.to_user_id(arg)

  body = utils.database_request(self,
                                'getprofile',
                                {'userid': arg})
  if body:
    html = '<div>'
    html += '  <div style="display: table-cell; width: 80px; vertical-align: top">'
    html += '    <img src="https://play.pokemonshowdown.com/sprites/{avatar_dir}/{avatar_name}.png"'
    html += '    width="80" height="80">'
    html += '  </div>'
    html += '  <div style="display: table-cell; width: 100%; vertical-align: top">'
    html += '    <b style="color: {name_color}">{nome}</b><br>{badges}'
    if body['descrizione'].strip() != '':
      html += '  <hr style="margin: 4px 0">'
      html += '  <div style="text-align: justify">{descrizione}</div>'
    html += '  </div>'
    html += '</div>'

    if body['avatar'][0] == '#':
      avatar_dir = 'trainers-custom'
      avatar_name = body['avatar'][1:]
    else:
      avatar_dir = 'trainers'
      avatar_name = body['avatar']

    nome = body['nome']

    name_color = utils.username_color(utils.to_user_id(nome))

    badges = ''
    badge = '<img src="{immagine}" width="12" height="12" title="{title}"'
    badge += ' style="border: 1px solid; border-radius: 2px; margin: 2px 1px 0 0;'
    badge += ' background: {sfondo}{opacity}">'
    title = 'Vincitore {seasonal} {anno}'
    for i in body['seasonal']:
      badges += badge.format(immagine=i['immagine'],
                             title=title.format(seasonal=i['seasonal'],
                                                anno=i['anno']),
                             sfondo=i['sfondo'],
                             opacity='')
    title = '{tier}:{dal}{al}'
    for i in body['elitefour'][:10]:
      if i['datafine'] is not None:
        opacity = '; opacity: .5'
      else:
        opacity = ''
      dal = ' dal {}'.format(utils.date_format(i['data']))
      if i['datafine'] is not None:
        al = ' al {}'.format(utils.date_format(i['datafine']))
      else:
        al = ''
      badges += badge.format(immagine=i['immagine'],
                             title=title.format(tier=i['tier'],
                                                dal=dal,
                                                al=al),
                             sfondo=i['sfondo'],
                             opacity=opacity)

    descrizione = body['descrizione'].replace('<', '&lt;')

    await self.send_htmlbox(room, html.format(avatar_dir=avatar_dir,
                                              avatar_name=avatar_name,
                                              name_color=name_color,
                                              nome=nome,
                                              badges=badges,
                                              descrizione=descrizione))


async def setprofile(self, room, user, arg):
  if room is not None and not utils.is_voice(user):
    return

  if len(arg) > 200:
    await self.send_reply(room, user, 'Errore: lunghezza massima 200 caratteri')
    return

  utils.database_request(self,
                         'setprofile',
                         {'userid': utils.to_user_id(user),
                          'descrizione': arg})

  await self.send_reply(room, user, 'Salvato')
