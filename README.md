# 💬 Real-Time Chat Application

A modern, full-stack real-time chat application built with **FastAPI** and **React**. Features WebSocket-based messaging, AI-powered chatbot integration, file sharing, room management, and production-ready Docker deployment with SSL.

![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=flat-square&logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-009688?style=flat-square&logo=fastapi&logoColor=white)
![React](https://img.shields.io/badge/React-19-61DAFB?style=flat-square&logo=react&logoColor=black)
![MongoDB](https://img.shields.io/badge/MongoDB-7.0-47A248?style=flat-square&logo=mongodb&logoColor=white)
![Redis](https://img.shields.io/badge/Redis-7-DC382D?style=flat-square&logo=redis&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-Compose-2496ED?style=flat-square&logo=docker&logoColor=white)

---

## ✨ Features

### Core Functionality
- **🔐 JWT Authentication** - Secure user registration and login with bcrypt password hashing
- **💬 Real-Time Messaging** - WebSocket-based instant messaging with typing indicators
- **🏠 Chat Rooms** - Create, join, and manage private chat rooms with invite codes
- **📁 File Sharing** - Upload and share images, documents, and files within rooms
- **🤖 AI Chatbot** - Integrated Google Gemini AI assistant (trigger with `/bot` or `@ai`)
- **👑 Admin Panel** - User management and system administration

### Technical Highlights
- **Scalable Architecture** - Redis pub/sub for multi-instance WebSocket synchronization
- **Production Ready** - Docker Compose deployment with Nginx reverse proxy
- **Auto SSL** - Let's Encrypt certificates with automatic renewal via Certbot
- **Responsive UI** - Modern React frontend with Vite for fast development
- **Comprehensive Testing** - Unit tests, API tests, and load testing included

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         NGINX (SSL/Proxy)                       │
│                     ┌─────────────────────┐                     │
│                     │   Port 80 / 443     │                     │
└─────────────────────┴─────────────────────┴─────────────────────┘
                              │
          ┌───────────────────┼───────────────────┐
          │                   │                   │
          ▼                   ▼                   ▼
┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐
│    Frontend     │  │    Backend      │  │    Certbot      │
│  (Static React) │  │   (FastAPI)     │  │  (SSL Renewal)  │
│                 │  │   Port 8000     │  │                 │
└─────────────────┘  └────────┬────────┘  └─────────────────┘
                              │
          ┌───────────────────┼───────────────────┐
          │                   │                   │
          ▼                   ▼                   ▼
┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐
│     MongoDB     │  │      Redis      │  │  File Storage   │
│   (Database)    │  │  (Pub/Sub +     │  │   (Uploads)     │
│   Port 27017    │  │    Cache)       │  │                 │
│                 │  │   Port 6379     │  │                 │
└─────────────────┘  └─────────────────┘  └─────────────────┘
```

---

## 📁 Project Structure

```
Real-Time-Chat/
├── 📄 main.py                 # FastAPI application entry point
├── 📄 docker-compose.yml      # Production deployment config
├── 📄 docker-compose.local.yml # Local development config
├── 📄 Dockerfile              # Backend container
├── 📄 nginx.conf              # Nginx configuration
├── 📄 requirements.txt        # Python dependencies
├── 📄 init-letsencrypt.sh     # SSL certificate setup script
│
├── 📂 auth/                   # Authentication module
│   └── core.py                # JWT tokens, password hashing, user validation
│
├── 📂 config/                 # Application configuration
│   └── database.py            # MongoDB connection and collections
│
├── 📂 models/                 # Pydantic data models
│   ├── user.py                # User model
│   ├── room.py                # Room model
│   └── file.py                # File metadata model
│
├── 📂 routes/                 # API route handlers
│   ├── auth.py                # /api/signup, /api/signin, /api/me
│   ├── chat.py                # /api/ws/{room_id}, /api/history/{room_id}
│   ├── rooms.py               # /api/rooms/*, room management
│   ├── files.py               # /api/files/*, file upload/download
│   └── admin.py               # /api/admin/*, user management
│
├── 📂 utils/                  # Utility modules
│   ├── ConnectionManager.py   # WebSocket connection management + Redis pub/sub
│   └── chatbot.py             # Google Gemini AI integration
│
├── 📂 frontend/               # React frontend application
│   ├── src/
│   │   ├── components/        # React components
│   │   │   ├── Chat.jsx       # Main chat interface
│   │   │   ├── SignIn.jsx     # Login page
│   │   │   ├── SignUp.jsx     # Registration page
│   │   │   ├── UserProfile.jsx # User profile page
│   │   │   └── AdminPanel.jsx # Admin management panel
│   │   ├── App.jsx            # Main application component
│   │   ├── AuthContext.jsx    # Authentication state management
│   │   ├── api.js             # Axios API configuration
│   │   └── App.css            # Styling
│   ├── package.json           # Node.js dependencies
│   ├── vite.config.js         # Vite build configuration
│   ├── Dockerfile             # Frontend container
│   └── nginx.conf             # Frontend Nginx config
│
├── 📂 tests/                  # Test suite
│   ├── test_auth.py           # Authentication tests
│   ├── test_rooms.py          # Room management tests
│   ├── test_files.py          # File upload tests
│   ├── test_api.py            # API endpoint tests
│   └── load_test.py           # Performance/load testing
│
└── 📂 certbot/                # SSL certificate storage
    ├── conf/                  # Let's Encrypt configuration
    └── www/                   # ACME challenge files
```

---

## 🚀 Getting Started

### Prerequisites

- **Docker** & **Docker Compose** (for production/containerized setup)
- **Python 3.11+** (for local development)
- **Node.js 18+** (for frontend development)
- **MongoDB 7.0** (local or cloud instance)
- **Redis 7** (for WebSocket scaling)

### Environment Variables

Create a `.env` file in the project root:

```bash
# MongoDB Configuration
MONGO_USERNAME=admin
MONGO_PASSWORD=your_secure_password
MONGO_URI=mongodb://admin:your_secure_password@mongodb:27017/realtime_chat?authSource=admin
DB_NAME=realtime_chat

# Security
SECRET_KEY=your-super-secret-jwt-key-change-this

# Admin User (auto-created on startup)
ADMIN_USERNAME=admin
ADMIN_PASSWORD=your_admin_password

# AI Chatbot (optional)
GEMINI_API_KEY=your_gemini_api_key

# CORS (comma-separated origins for production)
CORS_ORIGINS=https://yourdomain.com,https://www.yourdomain.com

# Redis (Docker uses internal URL)
REDIS_URL=redis://redis:6379

# File Uploads
UPLOAD_DIR=/app/uploads
```

---

## 🐳 Docker Deployment (Recommended)

### Quick Start (Production)

1. **Clone the repository:**
   ```bash
   git clone https://github.com/yourusername/Real-Time-Chat.git
   cd Real-Time-Chat
   ```

2. **Configure environment:**
   ```bash
   cp .env.example .env
   # Edit .env with your settings
   ```

3. **Initialize SSL certificates (first time only):**
   ```bash
   chmod +x init-letsencrypt.sh
   ./init-letsencrypt.sh
   ```

4. **Launch all services:**
   ```bash
   docker compose up -d
   ```

5. **Access the application:**
   - Frontend: `https://yourdomain.com`
   - API: `https://yourdomain.com/api`

### Local Development with Docker

```bash
docker compose -f docker-compose.local.yml up -d
```

- Frontend: `http://localhost`
- API: `http://localhost:8000`

---

## 💻 Local Development (Without Docker)

### Backend Setup

1. **Create virtual environment:**
   ```bash
   python -m venv venv
   source venv/bin/activate  # Linux/Mac
   # or
   .\venv\Scripts\activate   # Windows
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Start MongoDB and Redis** (local instances or containers):
   ```bash
   # Using Docker for just the databases
   docker run -d -p 27017:27017 --name mongo mongo:7.0
   docker run -d -p 6379:6379 --name redis redis:7-alpine
   ```

4. **Run the backend:**
   ```bash
   python main.py
   ```

### Frontend Setup

1. **Navigate to frontend directory:**
   ```bash
   cd frontend
   ```

2. **Install dependencies:**
   ```bash
   npm install
   ```

3. **Start development server:**
   ```bash
   npm run dev
   ```

4. **Access the app:**
   - Frontend: `http://localhost:5173`
   - API: `http://localhost:8000`

---

## 🔌 API Reference

### Authentication

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/signup` | Register new user |
| `POST` | `/api/signin` | Login and get JWT token |
| `GET` | `/api/me` | Get current user info |

### Chat & Rooms

| Method | Endpoint | Description |
|--------|----------|-------------|
| `WS` | `/api/ws/{room_id}?token=JWT` | WebSocket connection for real-time chat |
| `GET` | `/api/history/{room_id}` | Get last 50 messages |
| `GET` | `/api/rooms` | List user's rooms |
| `POST` | `/api/rooms/create` | Create new room |
| `POST` | `/api/rooms/join` | Join room via invite code |
| `DELETE` | `/api/rooms/{room_id}` | Delete room (owner only) |

### File Management

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/files/upload` | Upload file to room |
| `GET` | `/api/files/{file_id}` | Download file |
| `GET` | `/api/files/room/{room_id}` | List room files |

### Admin (Requires Admin Role)

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/admin/users` | List all users |
| `DELETE` | `/api/admin/users/{user_id}` | Delete user |

---

## 🤖 AI Chatbot

The application includes an integrated AI assistant powered by **Google Gemini**. To enable:

1. Get an API key from [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Add to your `.env` file:
   ```bash
   GEMINI_API_KEY=your_api_key_here
   ```

### Usage

Trigger the AI in any chat room:
- `/bot <your question>` - Direct command
- `@ai <your question>` - Mention trigger

The bot responds with helpful, concise answers and shows typing indicators while processing.

---

## 🧪 Testing

### Run All Tests

```bash
# Activate virtual environment first
pytest
```

### Run Specific Test Files

```bash
# Authentication tests
pytest tests/test_auth.py -v

# Room management tests
pytest tests/test_rooms.py -v

# File upload tests
pytest tests/test_files.py -v

# Load testing (requires running server)
python tests/load_test.py
```

### Test Configuration

Tests use `pytest.ini` for configuration. Key settings:
- Async support enabled via `anyio`
- Test isolation with fixtures in `conftest.py`

---

## 🔒 Security Features

- **Password Hashing** - bcrypt with automatic salt generation
- **JWT Tokens** - Short-lived access tokens (30 min default)
- **CORS Protection** - Configurable allowed origins
- **Room Privacy** - Membership-based access control
- **Input Validation** - Pydantic models for all inputs
- **SQL Injection Prevention** - MongoDB with parameterized queries
- **HTTPS Only** - Automatic SSL with Let's Encrypt

---

## 📊 WebSocket Message Types

### Client → Server

```json
// Chat message
{ "type": "chat", "msg": "Hello!", "file_id": "optional_file_id" }

// Typing indicator
{ "type": "typing", "status": true }
```

### Server → Client

```json
// Chat history (on connect)
{ "type": "history", "messages": [...] }

// New message
{ "type": "chat", "user": "username", "msg": "Hello!", "file_info": {...} }

// Typing indicator
{ "type": "typing", "user": "username", "status": true }

// System message
{ "type": "chat", "user": "system", "msg": "username joined" }
```

---

## 🔧 Configuration Options

| Variable | Default | Description |
|----------|---------|-------------|
| `HOST` | `127.0.0.1` | Backend host binding |
| `SECRET_KEY` | `your-secret-key` | JWT signing key |
| `MONGO_URI` | `mongodb://localhost:27017` | MongoDB connection string |
| `DB_NAME` | `realtime_chat` | Database name |
| `REDIS_URL` | `redis://localhost:6379` | Redis connection URL |
| `CORS_ORIGINS` | `*` | Allowed CORS origins (comma-separated) |
| `UPLOAD_DIR` | `./uploads` | File upload directory |
| `GEMINI_API_KEY` | - | Google Gemini API key (optional) |
| `ADMIN_USERNAME` | - | Auto-created admin username |
| `ADMIN_PASSWORD` | - | Auto-created admin password |

---

## 🛠️ Troubleshooting

### Common Issues

**WebSocket connection fails:**
- Ensure the JWT token is valid and not expired
- Check that the user is a member of the room
- Verify CORS origins include your frontend URL

**MongoDB connection errors:**
- Verify `MONGO_URI` is correct
- Check MongoDB is running and accessible
- Ensure username/password are correct

**Redis connection issues:**
- Confirm Redis is running on port 6379
- Check `REDIS_URL` environment variable
- WebSockets will still work (single instance mode)

**File uploads failing:**
- Verify `UPLOAD_DIR` exists and is writable
- Check file size limits in Nginx config
- Ensure proper permissions on upload directory

**AI Bot not responding:**
- Verify `GEMINI_API_KEY` is set correctly
- Check API key has sufficient quota
- Look for error messages in backend logs

---

## 📜 License

This project is open source and available under the [MIT License](LICENSE).

---

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

---

## 📧 Support

If you encounter any issues or have questions, please [open an issue](https://github.com/yourusername/Real-Time-Chat/issues) on GitHub.

---

<div align="center">
  <b>Built with ❤️ using FastAPI, React, and MongoDB</b>
</div>
