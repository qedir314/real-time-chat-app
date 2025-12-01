let ws;
let currentUsername = '';
let roomHistory = [];
let currentRoom = 'general';
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
    btn.onclick = () => switchRoomSafely(room);
    historyDiv.appendChild(btn);
  });
}

function switchRoomSafely(room) {
    clearTimeout(typingTimeout);
    typingUsers = {};

    // Send stop-typing and close after a small delay to ensure delivery
    if (ws && ws.readyState === WebSocket.OPEN) {
      ws.send(JSON.stringify({ type: 'typing', user: currentUsername, status: false }));
      setTimeout(() => {
        if (ws) ws.close();
        currentRoom = room;
        connect();
      }, 50);
    } else {
      currentRoom = room;
      connect();
    }
  }

async function fetchMe() {
    const response = await fetch("/me");
    if (response.ok) {
        const data = await response.json();
        currentUsername = data.username;
        document.getElementById('currentName').textContent = currentUsername;
    } else {
        window.location.href = "/signin";
    }
}

async function connect() {
    await fetchMe();

    if (!token) {
        window.location.href = "/signin";
        return;
    }

    if (!roomHistory.includes(currentRoom)) {
        roomHistory.push(currentRoom);
    }
    updateRoomHistory();

    const protocol = location.protocol === 'https:' ? 'wss://' : 'ws://';
    const wsUrl = `${protocol}${location.host}/ws/${encodeURIComponent(currentRoom)}?token=${token}`;
    ws = new WebSocket(wsUrl);

  ws.addEventListener('open', () => {
    log(`Connected to room: ${currentRoom}`);
    document.getElementById('sidebar').style.display = 'block';
    document.getElementById('chatBox').style.display = 'block';
    document.getElementById('switchRoomBox').style.display = 'none';
  });

  ws.addEventListener('message', (e) => {
    try {
      const obj = JSON.parse(e.data);
      if (obj.type === 'history') {
        logEl.textContent = '';
        obj.messages.forEach(msg => {
            log((msg.user || 'unknown') + ': ' + (msg.msg || ''));
        });
      }
      else if (obj.type === 'chat') {
        log((obj.user || 'unknown') + ': ' + (obj.msg || ''));
      } else if (obj.type === 'typing') {
        typingUsers[obj.user] = obj.status;
        updateTypingStatus();
      }
    } catch (err){
        console.error("Error parsing message:", err);
      log('Server: ' + e.data);
    }
  });

  ws.addEventListener('close', () => log('Disconnected'));
  ws.addEventListener('error', (ev) => log('WebSocket error'));
}

document.getElementById('send').onclick = () => {
    const input = document.getElementById('msg');
    if (!ws || ws.readyState !== WebSocket.OPEN) { log('Socket not open'); return; }
    const text = input.value.trim();
    if (!text) return;

    ws.send(JSON.stringify({ type: 'chat', msg: text }));
    input.value = '';
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

document.getElementById('logoutBtn').onclick = () => {
    document.cookie = "access_token=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=/";
    if (ws) {
        ws.close();
    }
    window.location.href = "/signin";
};

document.getElementById('newChatBtn').addEventListener('click', () => {
    document.getElementById('chatBox').style.display = 'none';
    document.getElementById('switchRoomBox').style.display = 'block';
});

document.getElementById('switchBtn').onclick = () => {
    const newRoom = (document.getElementById('newRoom').value || 'general').trim();
    switchRoomSafely(newRoom);
  };


window.addEventListener('load', connect);