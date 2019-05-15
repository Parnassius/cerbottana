const request = require('request');

global.Parser = {
  commands: {},
  parse: function(message) {
    if (!message) return;

    console.log(message);

    let parts = message.split('|');
    let first = parts[0].split('\n');
    let roomid = first[0].toLowerCase().replace(/[^a-z0-9-]/g, '') || 'lobby';

    switch (parts[1]) {
      case 'challstr':
        let challstr = parts.slice(2).join('|');

        request.post('http://play.pokemonshowdown.com/action.php', {
          headers: {
            'Content-Type': 'application/x-www-form-urlencoded'
          },
          body: 'act=login&name=' + process.env.USERNAME + '&pass=' + process.env.PASSWORD + '&challstr=' + challstr
        }, function(err, res, body) {
          if (!err && res.statusCode === 200) {
            if (body[0] === ']') {
              try {
                body = JSON.parse(body.substr(1));
              } catch (e) {}
              if (body.assertion && body.assertion[0] !== ';') {
                Chat.sendMessage(null, '/trn ' + process.env.USERNAME + ',0,' + body.assertion);
              } else {
                console.log('login failed');
                process.exit(0);
              }
            } else {
              console.log('invalid login request');
              process.exit(0);
            }
          }
        });
        break;
      case 'updateuser':
        if (parts[2] !== process.env.USERNAME) return;
        let rooms = (process.env.ROOMS + ',' + process.env.PRIVATE_ROOMS).replace(/^,|,$/g, '').split(',');
        for (let i = 0; i < rooms.length; i++) {
          Chat.sendMessage(null, '/join ' + rooms[i]);
        }
        break;
      case 'pm':
        if (toId(parts[2]) === toId(process.env.USERNAME)) return;
        this.parseMessage(parts[2], null, parts.splice(4).join('|').trim());
        break;
      case 'c':
        if (toId(parts[2]) === toId(process.env.USERNAME)) return;
        this.parseMessage(parts[2], roomid, parts.splice(3).join('|').trim());
        break;
      case 'c:':
        if (toId(parts[3]) === toId(process.env.USERNAME)) return;
        this.parseMessage(parts[3], roomid, parts.splice(4).join('|').trim());
        break;
    }
  },
  parseMessage(user, room, message) {
    if (message[0] === process.env.COMMAND_CHARACTER) {
      this.parseCommand(user, room, message.trim());
    } else if (room) {

    } else { // pm
      Chat.sendPM(user, "I'm a bot");
    }
  },
  parseCommand(user, room, message) {
    const command = message.split(' ')[0].substr(1);

    if (!this.commands[command]) {
      if (!room) {
        Chat.sendPM(user, 'Invalid command');
      }
      return;
    }

    this.commands[command](user, room, message.indexOf(' ') + 1);
  }
};
