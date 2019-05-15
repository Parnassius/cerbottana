const WebSocket = require('faye-websocket').Client;

const conn = new WebSocket("ws://" + process.env.SHOWDOWN_HOST + ":" + process.env.SHOWDOWN_PORT + "/showdown/websocket");

conn.onopen = function() {

};

conn.onerror = function(error) {
  process.exit(0);
};

conn.onclose = function(close) {
  process.exit(0);
};

conn.onmessage = function(message) {
  Parser.parse(message.data);
};

Connection = conn;
