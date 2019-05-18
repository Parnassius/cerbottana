const request = require('request');

process.on('uncaughtException', function(err) {
  console.log('uncaughtException: ' + err.stack);
});


String.prototype.removeAccents = function() {
  var text = this;
  text = text.replace(/à/g, 'a');
  text = text.replace(/è|é/g, 'e');
  text = text.replace(/ì/g, 'i');
  text = text.replace(/ò/g, 'o');
  text = text.replace(/ù/g, 'u');
  return text;
};

global.toId = function(text) {
  return text.toLowerCase().replace(/[^a-z0-9]/g, '');
};

global.isVoice = function(user) {
  return "+*%@★#&~".indexOf(user[0]) !== -1;
}

global.databaseRequest = function(action, params, callback) {
  request.post(process.env.DATABASE_API_URL, {
    form: Object.assign({
      key: process.env.DATABASE_API_KEY,
      action: action
    }, params)
  }, function(err, res, body) {
    if (!err && res.statusCode === 200) {
      try {
        body = JSON.parse(body);
      } catch (e) {}
      if (typeof body === 'object' && typeof callback === 'function') {
        callback(body);
      }
    }
  });
}

require('./chat.js');
require('./parser.js');

require('./server.js');

global.Connection = null;
require('./connection.js');
