import React, { useState, useEffect, useRef } from 'react';
import { useAuth } from '../AuthContext';
import api from '../api';

const Chat = () => {
  const { user, logout } = useAuth();
  const [messages, setMessages] = useState([]);
  const [rooms, setRooms] = useState(['general']);
  const [currentRoom, setCurrentRoom] = useState('general');
  const [message, setMessage] = useState('');
  const [typing, setTyping] = useState({});
  const socketRef = useRef(null);
  const messagesEndRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  useEffect(() => {
    const fetchRooms = async () => {
      try {
        const response = await api.get('/rooms');
        setRooms(response.data.rooms);
      } catch (err) {
        console.error('Failed to fetch rooms', err);
      }
    };
    fetchRooms();
  }, []);

  useEffect(() => {
    const token = localStorage.getItem('token');
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const host = window.location.host;
    // If running in dev mode (Vite), we might need to point to the backend port
    // But ideally we use a proxy in vite.config.js
    const wsUrl = `${protocol}//${host}/ws/${currentRoom}?token=${token}`;

    const socket = new WebSocket(wsUrl);
    socketRef.current = socket;

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

    socket.onclose = () => {
      console.log('WebSocket disconnected');
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
    if (socketRef.current) {
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

  return (
    <div className="chat-app">
      <header>
        <h1>Real-Time Chat</h1>
        <div className="user-info">
          <span>Welcome, {user.username.charAt(0).toUpperCase() + user.username.slice(1)}!</span>
          <button className="logout-btn" onClick={logout}>Logout</button>
        </div>
      </header>
      <div className="chat-container">
        <aside className="sidebar">
          <h3>Rooms</h3>
          <ul>
            {rooms.map((room) => (
              <li
                key={room}
                className={currentRoom === room ? 'active' : ''}
                onClick={() => setCurrentRoom(room)}
              >
                {room}
              </li>
            ))}
          </ul>
        </aside>
        <main className="chat-window">
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
        </main>
      </div>
    </div>
  );
};

export default Chat;
