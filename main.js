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

require('./chat.js');
require('./parser.js');

require('./server.js');

global.Connection = null;
require('./connection.js');
