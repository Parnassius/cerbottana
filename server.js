const http = require('http');

http.createServer(function(request, response) {
  res.writeHead(200, {'Content-Type': 'text/plain'});
  res.write('cerbottana');
  res.end();
}).listen(process.env.PORT || 5000);
