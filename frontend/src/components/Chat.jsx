import React, { useState, useEffect, useRef } from 'react';
import { useAuth } from '../AuthContext';
import api from '../api';

import { useNavigate } from 'react-router-dom';

const Chat = () => {
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  const [messages, setMessages] = useState([]);
  const [rooms, setRooms] = useState([]);
  const [currentRoom, setCurrentRoom] = useState(null);
  const [message, setMessage] = useState('');
  const [typing, setTyping] = useState({});
  
  // Modal states
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [createRoomName, setCreateRoomName] = useState('');
  const [createRoomPassword, setCreateRoomPassword] = useState('');
  
  const [showJoinModal, setShowJoinModal] = useState(false);
  const [joinInviteCode, setJoinInviteCode] = useState('');

  const socketRef = useRef(null);
  const messagesEndRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const fetchRooms = React.useCallback(async () => {
    try {
      const response = await api.get('/rooms');
      setRooms(response.data.rooms);
      // If current room is not set and we have rooms, set to first one
      if (!currentRoom && response.data.rooms.length > 0) {
        setCurrentRoom(response.data.rooms[0]);
      }
    } catch (err) {
      console.error('Failed to fetch rooms', err);
    }
  }, [currentRoom]);

  useEffect(() => {
    const init = async () => {
        await fetchRooms();
    };
    init();
  }, [fetchRooms]);

  useEffect(() => {
    if (!currentRoom) return;

    const token = localStorage.getItem('token');
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const host = window.location.host;
    const wsUrl = `${protocol}//${host}/api/ws/${currentRoom.room_id}?token=${token}`;

    if (socketRef.current) {
        socketRef.current.close();
    }

    const socket = new WebSocket(wsUrl);
    socketRef.current = socket;

    socket.onopen = () => {
        console.log("Connected to room", currentRoom.name);
    };

    socket.onmessage = (event) => {
      const data = JSON.parse(event.data);
      if (data.type === 'history') {
        setMessages(data.messages);
      } else if (data.type === 'chat') {
        setMessages((prev) => [...prev, data]);
      } else if (data.type === 'typing') {
        setTyping((prev) => ({
          ...prev,
          [data.user]: data.status,
        }));
      }
    };

    socket.onclose = (e) => {
      console.log('WebSocket disconnected', e.code);
    };

    return () => {
      socket.close();
    };
  }, [currentRoom]);

  const sendMessage = (e) => {
    e.preventDefault();
    if (message.trim() && socketRef.current) {
      socketRef.current.send(JSON.stringify({ type: 'chat', msg: message }));
      setMessage('');
      sendTyping(false);
    }
  };

  const sendTyping = (status) => {
    if (socketRef.current && socketRef.current.readyState === WebSocket.OPEN) {
      socketRef.current.send(JSON.stringify({ type: 'typing', status }));
    }
  };

  const handleTypingChange = (e) => {
    setMessage(e.target.value);
    if (e.target.value.length > 0) {
      sendTyping(true);
    } else {
      sendTyping(false);
    }
  };

  const handleCreateRoom = async (e) => {
      e.preventDefault();
      try {
          const payload = { name: createRoomName };
          if (createRoomPassword) payload.password = createRoomPassword;
          await api.post('/rooms/create', payload);
          setShowCreateModal(false);
          setCreateRoomName('');
          setCreateRoomPassword('');
          fetchRooms(); 
      } catch {
          alert("Failed to create room");
      }
  };

  const handleJoinRoom = async (e) => {
      e.preventDefault();
      try {
          const payload = { invite_code: joinInviteCode };
          await api.post('/rooms/join', payload);
          setShowJoinModal(false);
          setJoinInviteCode('');
          fetchRooms();
      } catch (err) {
          alert("Failed to join room: " + (err.response?.data?.detail || err.message));
      }
  };

  return (
    <div className="chat-app">
      <header>
        <h1>Real-Time Chat</h1>
        <div className="user-info">
          <span>{user.username}</span>
          {user.is_admin && (
            <button 
              className="logout-btn" 
              onClick={() => navigate('/admin')}
              style={{marginRight: '10px', borderColor: '#007bff', color: '#007bff'}}
            >
              Admin Panel
            </button>
          )}
          <button className="logout-btn" onClick={logout}>Logout</button>
        </div>
      </header>
      <div className="chat-container">
        <aside className="sidebar">
          <h3>Rooms</h3>
          <div className="sidebar-buttons">
              <button className="sidebar-btn" onClick={() => setShowCreateModal(true)}>+ New</button>
              <button className="sidebar-btn" onClick={() => setShowJoinModal(true)}>Join</button>
          </div>
          <ul>
            {rooms.map((room) => (
              <li
                key={room.room_id}
                className={currentRoom?.room_id === room.room_id ? 'active' : ''}
                onClick={() => setCurrentRoom(room)}
              >
                {room.name}
              </li>
            ))}
          </ul>
        </aside>
        <main className="chat-window">
          {currentRoom && (
              <>
                <div className="room-header" style={{padding: '10px 20px', borderBottom: '1px solid #eee', fontWeight: 'bold'}}>
                    {currentRoom.name}
                    {currentRoom.invite_code && (
                        <span style={{marginLeft: '20px', fontSize: '0.8em', color: '#666'}}>
                            Invite: {currentRoom.invite_code}
                        </span>
                    )}
                </div>
                <div className="messages">
                    {messages.map((msg, index) => (
                    <div
                        key={index}
                        className={`message ${msg.user === user.username ? 'own' : ''} ${
                        msg.user === 'system' ? 'system' : ''
                        } ${msg.user === 'AI_Bot' ? 'bot' : ''}`}
                    >
                        <strong>{msg.user}:</strong> {msg.msg}
                    </div>
                    ))}
                    {Object.entries(typing).map(([u, isTyping]) => (
                    isTyping && u !== user.username && (
                        <div key={u} className="typing-indicator">
                        {u} is typing...
                        </div>
                    )
                    ))}
                    <div ref={messagesEndRef} />
                </div>
                <form onSubmit={sendMessage} className="message-form">
                    <input
                    type="text"
                    placeholder="Type a message..."
                    value={message}
                    onChange={handleTypingChange}
                    onBlur={() => sendTyping(false)}
                    />
                    <button type="submit">Send</button>
                </form>
              </>
          )}
          {!currentRoom && (
              <div style={{display: 'flex', alignItems: 'center', justifyContent: 'center', height: '100%', color: '#888'}}>
                  Select or create a room to start chatting.
              </div>
          )}
        </main>
      </div>

      {showCreateModal && (
          <div className="modal-overlay" onClick={() => setShowCreateModal(false)}>
              <div className="modal-content" onClick={e => e.stopPropagation()}>
                  <h3>Create Room</h3>
                  <form onSubmit={handleCreateRoom}>
                      <input 
                        type="text" 
                        placeholder="Room Name" 
                        value={createRoomName} 
                        onChange={e => setCreateRoomName(e.target.value)}
                        required 
                      />
                      <input 
                        type="password" 
                        placeholder="Password (Optional)" 
                        value={createRoomPassword} 
                        onChange={e => setCreateRoomPassword(e.target.value)}
                      />
                      <div className="modal-buttons">
                          <button type="button" onClick={() => setShowCreateModal(false)} style={{background: '#ccc'}}>Cancel</button>
                          <button type="submit">Create</button>
                      </div>
                  </form>
              </div>
          </div>
      )}

      {showJoinModal && (
          <div className="modal-overlay" onClick={() => setShowJoinModal(false)}>
              <div className="modal-content" onClick={e => e.stopPropagation()}>
                  <h3>Join Room</h3>
                  <form onSubmit={handleJoinRoom}>
                      <input 
                        type="text" 
                        placeholder="Invite Code" 
                        value={joinInviteCode} 
                        onChange={e => setJoinInviteCode(e.target.value)}
                        required 
                      />
                      <div className="modal-buttons">
                          <button type="button" onClick={() => setShowJoinModal(false)} style={{background: '#ccc'}}>Cancel</button>
                          <button type="submit">Join</button>
                      </div>
                  </form>
              </div>
          </div>
      )}
    </div>
  );
};

export default Chat;