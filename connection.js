const WebSocket = require('faye-websocket').Client;

function connect() {
  const conn = new WebSocket("ws://" + process.env.HOST + ":" + process.env.PORT + "/showdown/websocket");

  conn.onopen = function() {

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
