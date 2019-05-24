const request = require('request');

require('./utils.js');

require('./chat.js');
require('./parser.js');

require('./server.js');

global.Connection = null;
require('./connection.js');
