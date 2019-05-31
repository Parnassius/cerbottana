Parser.commands.leaderboard = function(user, room, arg) {
  if (room === null || !isVoice(user)) return false;

  databaseRequest('getleaderboard', {}, function(body) {
    if (body.length === 0) {
      return Chat.sendMessage(room, 'Nessun risultato trovato');
    }

    let html = '<div style="max-height: 250px; overflow-y: auto">';
      html += '<div style="text-align: center"><b><big>';
        html += body[0].descrizione.replace(/</g, '&lt;') + ' ' + body[0].anno + ' - Fase 1';
      html += '</big></b></div>';
      html += '<hr style="margin-bottom: 0">';
      html += '<table style="width: 100%">';
        html += '<thead>';
          html += '<tr style="text-align: left">';
            html += '<th>#</th>';
            html += '<th>Utente</th>';
            html += '<th style="text-align: center">Punteggio</th>';
          html += '</tr>';
        html += '</thead>';
        html += '<tbody>';
          let pos = 0;
          let ties = 0;
          for (let i = 0; i < body.length; i++) {
            if (i === 0 || parseInt(body[i].punteggio) < parseInt(body[i - 1].punteggio)) {
              pos += ties + 1;
              ties = 0;
            } else {
              ties++;
            }
            html += '<tr>';
              html += '<td colspan="3">';
                html += '<hr style="margin: 0">';
              html += '</td>';
            html += '</tr>';
            html += '<tr';
            if (pos > 8) {
              html += ' style="opacity: .5"';
            }
            html += '>';
              html += '<td>' + pos + '</td>';
              html += '<td>' + body[i].utente.replace(/</g, '&lt;') + '</td>';
              html += '<td style="text-align: center">' + body[i].punteggio + '</td>';
            html += '</tr>';
          }
        html += '</tbody>';
      html += '</table>';
    html += '</div>';
    Chat.sendHTMLBox(room, html);
  });

  return false;
};
