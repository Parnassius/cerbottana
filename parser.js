const fs = require('fs');
const request = require('request');

global.Parser = {
  commands: {},
  parse: function(message) {
    if (!message) return;

    const parts = message.split('|');
    const first = parts[0].split('\n');
    const roomid = first[0].toLowerCase().replace(/[^a-z0-9-]/g, '') || 'lobby';

    switch (parts[1]) {
      case 'challstr':
        const challstr = parts.slice(2).join('|');

        request.post('https://play.pokemonshowdown.com/action.php', {
          headers: {
            'Content-Type': 'application/x-www-form-urlencoded',
          },
          body: 'act=login&name=' + process.env.USERNAME + '&pass=' + process.env.PASSWORD + '&challstr=' + challstr,
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
        if (typeof process.env.AVATAR !== 'undefined') {
          Chat.sendMessage(null, '/avatar ' + process.env.AVATAR);
        }
        const rooms = (process.env.ROOMS + ',' + process.env.PRIVATE_ROOMS).replace(/^,|,$/g, '').split(',');
        for (let i = 0; i < rooms.length; i++) {
          Chat.sendMessage(null, '/join ' + rooms[i]);
        }
        break;
      case 'J':
      case 'j':
        this.addUser(parts[2]);
        break;
      case 'L':
      case 'l':
        //
        break;
      case 'N':
      case 'n':
        this.addUser(parts[2]);
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
      case 'init':
        this.addUsers(parts[6].trim().split(',').slice(1));
        break;
      case 'queryresponse':
        this.parseQueryresponse(parts[2], parts[3]);
        break;
    }
  },
  addUser: function(user) {
    databaseRequest('adduser', {
      userid: toId(user),
      nome: user.substr(1),
    }, function(body) {
      if (body.needs_avatar === 1) {
        Chat.sendMessage(null, '/cmd userdetails ' + user);
      }
    });

    if (process.env.ADMINISTRATORS.split(',').indexOf(toId(user)) !== -1) {
      databaseRequest('getunapprovedprofiles', {
        user: toId(user)
      }, function(body) {
        if (body.num) {
          Chat.sendPM(user, 'Ci sono ' + body.num + ' profili in attesa di approvazione. Usa .token per approvarli o rifiutarli.');
        }
      });
    }
  },
  addUsers: function(users) {
    const self = this;
    const interval = setInterval(function() {
      if (users.length === 0) {
        return clearInterval(interval);
      }
      self.addUser(users.shift());
    }, 1000);
  },
  parseMessage: function(user, room, message) {
    if (message[0] === process.env.COMMAND_CHARACTER) {
      this.parseCommand(user, room, message.trim());
    } else if (room) {

    } else { // pm
      Chat.sendPM(user, 'I\'m a bot');
    }
  },
  parseCommand: function(user, room, message) {
    let command = message.split(' ')[0].substr(1).toLowerCase();

    if (typeof this.commands[command] === 'string') {
      command = this.commands[command];
    }

    if (typeof this.commands[command] !== 'function') {
      if (!room) {
        Chat.sendPM(user, 'Invalid command');
      }
      return;
    }

    const result = this.commands[command](user, room, message.substr(command.length + 2).trim());
    if (result) {
      if (room === null || result.pm) {
        Chat.sendPM(user, result.msg);
      } else {
        Chat.sendMessage(room, result.msg);
      }
    }
  },
  parseQueryresponse: function(cmd, data) {
    switch (cmd) {
      case 'userdetails':
        try {
          data = JSON.parse(data);
        } catch (e) {}
        if (typeof data === 'object' && data.avatar) {
          const userid = data.userid;
          let avatar = data.avatar;
          if (avatarIDs[avatar]) {
            avatar = avatarIDs[avatar];
          }
          databaseRequest('setavatar', {
            userid: userid,
            avatar: avatar,
          });
        }
        break;
    }
  },
};

const loadCommands = function() {
  const files = fs.readdirSync('./commands');
  for (let i = 0; i < files.length; i++) {
    require('./commands/' + files[i]);
  }
};

loadCommands();
