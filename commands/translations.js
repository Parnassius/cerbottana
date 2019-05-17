Parser.commands.trad = function(user, room, arg) {
  return;
  // controlla permessi

  const parola = arg.toLowerCase().replace(/[^a-z0-9àèéìòù]/g, '');
  if (parola == '') {
    return Chat.sendMessage(room, 'Cosa devo tradurre?');
  }
  // aliases ?

  let results = [];

  for (let i in translations) {
    for (let j = 0; j < translations[i].length; j++) {
      if (translations[i][j].en.toLowerCase().replace(/[^a-z0-9àèéìòù]/g, '') === parola) {
        results.push({
          trad: translations[i][j].it,
          cat: i
        });
      } else if (translations[i][j].it.toLowerCase().replace(/[^a-z0-9àèéìòù]/g, '') === parola) {
        results.push({
          trad: translations[i][j].en,
          cat: i
        });
      }
    }
  }

  if (results.length) {
    if (results.length === 1) {
      return Chat.sendMessage(room, results[0].trad);
    }
    var resultstext = '';
    for (let i = 0; i < results.length; i++) {
      if (i !== 0) resultstext += ', ';
      resultstext += results[i].trad + ' (' + results[i].cat + ')';
    }
    return Chat.sendMessage(room, resultstext);
  }
  return Chat.sendMessage(room, 'Non trovato');
};


const translations = {
  ability: [
  {en: 'Mickey Mouse', it: 'Topolino'}
  ],
  move: [
  {en: 'Mickey Mouse', it: 'Topolinoddd'}
  ]
};
