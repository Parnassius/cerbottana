Parser.commands.token = function(user, room, arg) {
  if (process.env.ADMINISTRATORS.split(',').indexOf(toId(user)) === -1) return false;

  const token = Server.createToken();
  return {msg: process.env.DATABASE_API_URL + 'dashboard.php?token=' + token, pm: true};
};
