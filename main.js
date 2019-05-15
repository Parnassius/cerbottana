global.toId = function(text) {
  return text.toLowerCase().replace(/[^a-z0-9]/g, '');
};

require('./chat.js');
require('./parser.js');

global.Connection = null;
require('./connection.js');
