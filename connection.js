const WebSocket = require('faye-websocket').Client;

function connect() {
  console.log('opening connection');
  const conn = new WebSocket("ws://" + process.env.HOST + ":" + process.env.PORT + "/showdown/websocket");

  conn.onopen = function() {
    console.log('connection open');
  };

  conn.onerror = function(error) {
    setTimeout(connect, 15000);
  };

  conn.onclose = function(close) {
    setTimeout(connect, 15000);
  };

  conn.onmessage = function(message) {
    Parser.parse(message.data);
  };

  Connection = conn;
}

connect();
