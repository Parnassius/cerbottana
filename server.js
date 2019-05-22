const crypto = require('crypto');
const http = require('http');

global.Server = {
  createToken: function() {
    const token = crypto.randomBytes(16).toString('hex');
    databaseRequest('newtoken', {
      token: token
    });
    return token;
  }
};

http.createServer(function(req, res) {
  res.writeHead(200, {'Content-Type': 'text/plain'});
  res.write('cerbottana');
  res.end();
}).listen(process.env.PORT || 5000);
