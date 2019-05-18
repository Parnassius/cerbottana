const THROTTLE_DELAY = 300;

global.Chat = {
  lastMessage: 0,
  sendQueue: [],
  sendHTMLBox: function(room, message) {
    this.sendMessage(room, '/addhtmlbox ' + message);
  },
  sendMessage: function(room, message) {
    this.send((room || '') + '|' + message);
  },
  sendPM: function(user, message) {
    this.send('|/w ' + user + ', ' + message);
  },
  send: function(message) {
    this.sendQueue.push(message);
    this.processQueue();
  },
  processQueue: function() {
    if (this.sendQueue.length === 0) return;
    let now = Date.now();
    if (this.lastMessage + THROTTLE_DELAY < now) {
      let msg = this.sendQueue.shift();
      Connection.send(msg);
      this.lastMessage = now;
    }
  }
};

setInterval(function() {
  Chat.processQueue();
}, THROTTLE_DELAY);
