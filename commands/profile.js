Parser.commands.profile = function(user, room, arg) {
  return false;
  if (room === null || !isVoice(user)) return false;

  if (arg.trim() === '') {
    arg = user;
  }

  arg = toId(arg);

  databaseRequest('getprofile', {
    userid: arg
  }, function(body) {
    let html = '<div style="display: flex">';
      html += '<div>';
        html += '<img src="https://play.pokemonshowdown.com/sprites/';
        if (body.avatar[0] === '#') {
          html += 'trainers-custom/' + body.avatar.substr(1);
        } else {
          html += 'trainers/' + body.avatar;
        }
        html += '.png" width="80" height="80">';
      html += '</div>';
      html += '<div>';
        html += body.descrizione.replace(/</g, '&lt;');
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
