let ws;
let currentUsername = '';
let roomHistory = [];
let currentRoom = '';
let typingUsers = {};
let typingTimeout;
const logEl = document.getElementById('log');
const typingStatusEl = document.getElementById('typingStatus');

function log(t) {
  logEl.textContent += t + '\n';
  logEl.scrollTop = logEl.scrollHeight;
}

  function updateTypingStatus() {
    const typingList = Object.keys(typingUsers).filter(user => typingUsers[user] && user !== currentUsername);
    typingStatusEl.textContent = typingList.length > 0 ? typingList.join(', ') + ' is typing...' : '';
  }

function updateRoomHistory() {
  const historyDiv = document.getElementById('roomHistory');
  historyDiv.innerHTML = '';
  roomHistory.forEach(room => {
    const btn = document.createElement('button');
    btn.className = 'room-btn' + (room === currentRoom ? ' active' : '');
    btn.textContent = room;
    btn.onclick = () => {
        clearTimeout(typingTimeout);
        if (ws && ws.readyState === WebSocket.OPEN) {
          ws.send(JSON.stringify({ type: 'typing', user: currentUsername, status: false }));
        }
        if (ws) ws.close();
        connect(room, currentUsername);
      };
    historyDiv.appendChild(btn);
  });
}

function switchRoomSafely(room, name) {
    clearTimeout(typingTimeout);
    typingUsers = {};

    // Send stop-typing and close after a small delay to ensure delivery
    if (ws && ws.readyState === WebSocket.OPEN) {
      ws.send(JSON.stringify({ type: 'typing', user: currentUsername, status: false }));
      setTimeout(() => {
        if (ws) ws.close();
        connect(room, name);
      }, 50);
    } else {
      connect(room, name);
    }
  }

function connect(room, name) {
  currentRoom = room;
  typingUsers = {};
  if (!roomHistory.includes(room)) {
    roomHistory.push(room);
  }
  updateRoomHistory();

  const protocol = location.protocol === 'https:' ? 'wss://' : 'ws://';
  ws = new WebSocket(protocol + location.host + '/ws/' + encodeURIComponent(room) + '/' + encodeURIComponent(name));

  ws.addEventListener('open', () => {
    document.getElementById('joinBox').style.display = 'none';
    document.getElementById('switchRoomBox').style.display = 'none';
    document.getElementById('chatBox').style.display = 'block';
    document.getElementById('sidebar').style.display = 'block';
    logEl.textContent = '';
    log('Connected to room: ' + room + ' as ' + name);
  });

  ws.addEventListener('message', (e) => {
    try {
      const obj = JSON.parse(e.data);
      if (obj.type === 'chat') {
        log((obj.user || 'unknown') + ': ' + (obj.msg || ''));
      } else if (obj.type === 'typing') {
        typingUsers[obj.user] = obj.status;
        updateTypingStatus();
      }
    } catch {
      log('Server: ' + e.data);
    }
  });

  ws.addEventListener('close', () => log('Disconnected'));
  ws.addEventListener('error', (ev) => log('WebSocket error'));
}

document.getElementById('join').onclick = () => {
  const room = (document.getElementById('room').value || 'general').trim();
  const name = (document.getElementById('name').value || 'anonymous').trim();
  currentUsername = name;
  connect(room, name);
};

function updateRoomHistory() {
    const historyDiv = document.getElementById('roomHistory');
    historyDiv.innerHTML = '';
    roomHistory.forEach(room => {
      const btn = document.createElement('button');
      btn.className = 'room-btn' + (room === currentRoom ? ' active' : '');
      btn.textContent = room;
      btn.onclick = () => switchRoomSafely(room, currentUsername);
      historyDiv.appendChild(btn);
    });
  }

  document.getElementById('newChatBtn').onclick = () => {
    clearTimeout(typingTimeout);
    if (ws && ws.readyState === WebSocket.OPEN) {
      ws.send(JSON.stringify({ type: 'typing', user: currentUsername, status: false }));
      setTimeout(() => {
        if (ws) ws.close();
        document.getElementById('chatBox').style.display = 'none';
        document.getElementById('switchRoomBox').style.display = 'block';
        document.getElementById('currentName').textContent = currentUsername;
        document.getElementById('newRoom').value = 'general';
        logEl.textContent = '';
      }, 50);
    }
  };

document.getElementById('switchBtn').onclick = () => {
    const newRoom = (document.getElementById('newRoom').value || 'general').trim();
    switchRoomSafely(newRoom, currentUsername);
  };

document.getElementById('send').onclick = () => {
    const input = document.getElementById('msg');
    if (!ws || ws.readyState !== WebSocket.OPEN) { log('Socket not open'); return; }
    const text = input.value.trim();
    if (!text) return;

    // Send stop-typing first
    ws.send(JSON.stringify({ type: 'typing', user: currentUsername, status: false }));
    clearTimeout(typingTimeout);

    // Then send the chat message
    ws.send(JSON.stringify({ type: 'chat', user: currentUsername, msg: text }));
    input.value = '';
    typingUsers[currentUsername] = false;
    updateTypingStatus();
  };

document.getElementById('msg').addEventListener('keydown', (e) => {
    if (e.key === 'Enter') {
      document.getElementById('send').click();
    } else {
      if (!ws || ws.readyState !== WebSocket.OPEN) return;
      clearTimeout(typingTimeout);
      ws.send(JSON.stringify({ type: 'typing', user: currentUsername, status: true }));
      typingTimeout = setTimeout(() => {
        ws.send(JSON.stringify({ type: 'typing', user: currentUsername, status: false }));
      }, 1000);
    }
  });