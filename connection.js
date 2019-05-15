const WebSocket = require('faye-websocket').Client;

function connect() {
  const conn = new WebSocket("ws://" + process.env.SHOWDOWN_HOST + ":" + process.env.SHOWDOWN_PORT + "/showdown/websocket");

  conn.onopen = function() {
    console.log('connection open');
  };

  conn.onerror = function(error) {
    console.log('error');
    setTimeout(connect, 15000);
  };

  conn.onclose = function(close) {
    console.log('close');
    setTimeout(connect, 15000);
  };

  conn.onmessage = function(message) {
    console.log('message: ' + message.data);
    Parser.parse(message.data);
  };

  Connection = conn;
}

connect();
