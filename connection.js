const WebSocket = require('faye-websocket').Client;

const connect = function() {

  const conn = new WebSocket((process.env.SHOWDOWN_PORT === "443" ? 'wss' : 'ws') + "://" + process.env.SHOWDOWN_HOST + ":" + process.env.SHOWDOWN_PORT + "/showdown/websocket");

  conn.onopen = function() {

  };

  conn.onerror = function(error) {
    setTimeout(connect, 15 * 1000);
  };

  conn.onclose = function(close) {
    setTimeout(connect, 15 * 1000);
  };

  conn.onmessage = function(message) {
    Parser.parse(message.data);
  };

  Connection = conn;

};

connect();
