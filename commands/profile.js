Parser.commands.campione = 'champion';
Parser.commands.champion = function(user, room, arg) {
  return this.elitefour(user, room, 'ou');
};
Parser.commands.e4 = 'elitefour';
Parser.commands.elite4 = 'elitefour';
Parser.commands.super4 = 'elitefour';
Parser.commands.superquattro = 'elitefour';
Parser.commands.elitefour = function(user, room, arg) {
  return false;
  if (room !== null && !isVoice(user)) return false;

  let self = this;
  databaseRequest('getelitefour', {
    tier: toId(arg)
  }, function(body) {
    if (body.length === 1) {
      if (room !== null && isVoice(user)) {
        if (typeof body[0].utente === 'string') {
          self.profile(user, room, body[0].utente);
        }
      } else {
        Chat.sendPM(user, body[0].utente);
      }
    } else if (body.length > 1) {
      let text = '';
      for (let i = 0; i < body.length; i++) {
        if (text !== '') {
          text += ' - ';
        }
        text += body[i].tier + ': ' + body[i].utente;
      }
      if (room !== null && isVoice(user)) {
        Chat.sendMessage(room, text);
      } else {
        Chat.sendPM(user, text);
      }
    }
  });

  return false;
};
Parser.commands.profile = function(user, room, arg) {
  if (room === null || !isVoice(user)) return false;

  if (arg.trim() === '') {
    arg = user;
  }

  arg = toId(arg);

  databaseRequest('getprofile', {
    userid: arg
  }, function(body) {
    let html = '<div>';
      html += '<div style="display: table-cell; width: 80px; vertical-align: top">';
        html += '<img src="https://play.pokemonshowdown.com/sprites/';
        if (body.avatar[0] === '#') {
          html += 'trainers-custom/' + body.avatar.substr(1);
        } else {
          html += 'trainers/' + body.avatar;
        }
        html += '.png" width="80" height="80">';
      html += '</div>';
      html += '<div style="display: table-cell; width: 100%; vertical-align: top">';
        html += '<b>' + body.nome + '</b><br>';
        for (let i = 0; i < body.elitefour.length; i++) {
          let title = body.elitefour[i].tier + ':';
          title += ' dal ' + dateFormat(body.elitefour[i].data);
          if (body.elitefour[i].datafine !== null) {
            title += ' al ' + dateFormat(body.elitefour[i].datafine);
          }
          html += '<img src="' + body.elitefour[i].immagine + '" width="12" height="12" title="' + title + '" style="border: 1px solid; border-radius: 2px; margin: 2px 1px 0 0' + (body.elitefour[i].datafine !== null ? '; opacity: .5' : '') + '">';
        }
        if (body.descrizione.trim() !== '') {
          html += '<hr style="margin: 4px 0">';
          html += '<div style="text-align: justify">';
            html += body.descrizione.replace(/</g, '&lt;');
          html += '</div>';
        }
      html += '</div>';
    html += '</div>';
    Chat.sendHTMLBox(room, html);
  });

  return false;
};

Parser.commands.setprofile = function(user, room, arg) {
  if (room !== null && !isVoice(user)) return false;

  if (arg.length > 200) {
    return {msg: 'Errore: lunghezza massima 200 caratteri'};
  }

  databaseRequest('setprofile', {
    userid: toId(user),
    descrizione: arg
  });

  return {msg: 'Salvato'};
};

Parser.commands.token = function(user, room, arg) {
  const allowedUsers = [
    'aethernum',
    'parnassius'
  ];

  if (allowedUsers.indexOf(toId(user)) === -1) return false;

  let token = Server.createToken();
  return {msg: process.env.DATABASE_API_URL + 'dashboard.php?token=' + token, pm: true};
};
