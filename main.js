process.on('uncaughtException', function(err, origin) {
  Connection.close();
  databaseRequest('logerror', {
    err: err.stack.toString(),
  }, function() {
    restartBot();
  });
  setTimeout(function() {
    restartBot();
  }, 15 * 1000);
});

require('./utils.js');

require('./chat.js');
require('./parser.js');

require('./server.js');

global.Connection = null;
require('./connection.js');
