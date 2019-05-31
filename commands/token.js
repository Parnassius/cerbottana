Parser.commands.token = function(user, room, arg) {
  const allowedUsers = [
    'aethernum',
    'parnassius'
  ];

  if (allowedUsers.indexOf(toId(user)) === -1) return false;

  let token = Server.createToken();
  return {msg: process.env.DATABASE_API_URL + 'dashboard.php?token=' + token, pm: true};
};
