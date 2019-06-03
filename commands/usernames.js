Parser.commands.acher = function(user, room, arg) {
  if (room !== null && !isVoice(user)) return false;
  return {msg: 'lo acher che bontà ♫'};
};

Parser.commands.aeth = 'aethernum';
Parser.commands.eterno = 'aethernum';
Parser.commands.aethernum = function(user, room, arg) {
  if (room !== null && !isVoice(user)) return false;
  return {msg: 'da decidere'};
};

Parser.commands.alpha = 'alphawittem';
Parser.commands.wittem = 'alphawittem';
Parser.commands.alphawittem = function(user, room, arg) {
  if (room !== null && !isVoice(user)) return false;
  return {msg: 'Italian luck jajaja'};
};

Parser.commands.cinse = 'consecutio';
Parser.commands.cobse = 'consecutio';
Parser.commands.conse = 'consecutio';
Parser.commands.consecutio = function(user, room, arg) {
  if (room !== null && !isVoice(user)) return false;
  const text = 'opss' + ['', 's', 'ss', 'sss'][Math.floor(Math.random() * 4)];
  return {msg: text + ' ho lasciato il pc acceso tutta notte'};
};

Parser.commands.duck = function(user, room, arg) {
  if (room !== null && !isVoice(user)) return false;
  return {msg: 'quack'};
};

Parser.commands.ed = 'edgummet';
Parser.commands.edgummet = function(user, room, arg) {
  if (room !== null && !isVoice(user)) return false;
  return {msg: 'soccontro'};
};

Parser.commands.francy = 'francyy';
Parser.commands.francyy = function(user, room, arg) {
  if (room !== null && !isVoice(user)) return false;
  return {msg: 'ei qualcuno ha qualche codice tcgo??? :3'};
};

Parser.commands.haund = function(user, room, arg) {
  if (room !== null && !isVoice(user)) return false;
  return {msg: '( ͡° ͜ʖ ͡°)'};
};

Parser.commands.howkings = function(user, room, arg) {
  if (room !== null && !isVoice(user)) return false;
  return {msg: 'Che si vinca o si perda, v0lca merda :3'};
};

Parser.commands.infli = 'inflikted';
Parser.commands.inflikted = function(user, room, arg) {
  if (room !== null && !isVoice(user)) return false;
  const text = 'INFLIKTED'.split('').sort(function(a, b) {
    return Math.random() - 0.5;
  }).join('');
  return {msg: 'ciao ' + text};
};

Parser.commands.lange = function(user, room, arg) {
  if (room !== null && !isVoice(user)) return false;
  return {msg: 'Haund mi traduci questo post?'};
};

Parser.commands.milak = function(user, room, arg) {
  if (room !== null && !isVoice(user)) return false;
  return {msg: 'No Maria io esco'};
};

Parser.commands.mister = function(user, room, arg) {
  if (room !== null && !isVoice(user)) return false;
  return {msg: 'Master'};
};
Parser.commands.mistercantiere = function(user, room, arg) {
  if (room !== null && !isVoice(user)) return false;
  return {msg: 'MasterCantiere'};
};

Parser.commands.azys = 'oizys';
Parser.commands.oizys = function(user, room, arg) {
  if (room !== null && !isVoice(user)) return false;
  return {msg: 'no'};
};

Parser.commands.rospe = 'r0spe';
Parser.commands.r0spe = function(user, room, arg) {
  if (room !== null && !isVoice(user)) return false;
  return {msg: 'buondì'};
};

Parser.commands.silver = 'silver97';
Parser.commands.silver97 = function(user, room, arg) {
  if (room !== null && !isVoice(user)) return false;
  const tiers = [
    'OU', 'Ubers', 'UU', 'RU', 'NU', 'PU', 'LC', 'Monotype', 'Anything Goes',
    '1v1', 'ZU', 'CAP', 'Doubles OU', 'Doubles Ubers', 'Doubles UU', 'VGC',
  ];
  const tier = tiers[Math.floor(Math.random() * tiers.length)];
  const text = 'qualcuno mi passa un team ' + tier;
  return {msg: text};
};

Parser.commands.smilzo = function(user, room, arg) {
  if (room !== null && !isVoice(user)) return false;
  return {msg: 'mai na gioia'};
};

Parser.commands.spec = 'specn';
Parser.commands.specn = function(user, room, arg) {
  if (room !== null && !isVoice(user)) return false;
  return {msg: 'Vi muto tutti'};
};

Parser.commands.cul1 = 'swculone';
Parser.commands.culone = 'swculone';
Parser.commands.kul1 = 'swculone';
Parser.commands.swcul1 = 'swculone';
Parser.commands.swkul1 = 'swculone';
Parser.commands.swculone = function(user, room, arg) {
  if (room !== null && !isVoice(user)) return false;
  return {msg: 'hue'};
};

Parser.commands.quas = 'thequasar';
Parser.commands.quasar = 'thequasar';
Parser.commands.thequasar = function(user, room, arg) {
  if (room !== null && !isVoice(user)) return false;
  return {msg: 'Basta con le pupazzate'};
};

Parser.commands['3v'] = 'trev';
Parser.commands.vvv = 'trev';
Parser.commands.trev = function(user, room, arg) {
  if (room !== null && !isVoice(user)) return false;
  return {msg: 'gioco di merda'};
};

Parser.commands.usy = 'uselesstrainer';
Parser.commands.uselesstrainer = function(user, room, arg) {
  if (room !== null && !isVoice(user)) return false;
  return {msg: 'kek'};
};

Parser.commands.volca = 'v0lca';
Parser.commands.v0lca = function(user, room, arg) {
  if (room !== null && !isVoice(user)) return false;
  return {msg: 'Porco mele...'};
};
