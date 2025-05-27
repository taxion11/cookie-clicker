# 🍪 Cookie Clicker Game

A modern, scalable cookie clicker game built with Go + Python microservices architecture, deployed on AWS ECS.

## 🚀 Quick Start

```bash
# Clone the repository
git clone <repository-url>
cd cookie-clicker-game

# Setup development environment
make setup

# Start development servers
make run

# Access the game
# 🌐 Game: http://localhost:8080
# 🐍 API: http://localhost:8001/docs
```

## 🏗️ Architecture

### Tech Stack
- **Frontend**: Go + Gin Framework + HTML/CSS/JavaScript
- **Backend**: Python + FastAPI
- **Database**: PostgreSQL + Redis
- **Infrastructure**: AWS ECS + ECR + RDS + ALB
- **CI/CD**: GitHub Actions
- **Reverse Proxy**: Nginx (production)

### Services
```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Nginx Proxy   │────│   Go Frontend   │────│  Python API     │
│   (Port 80)     │    │   (Port 8080)   │    │  (Port 8001)    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                                        │
                                              ┌─────────────────┐
                                              │   PostgreSQL    │
                                              │   (Port 5432)   │
                                              └─────────────────┘
```

## 🎮 Game Features

### Core Gameplay
- 🍪 **Cookie Clicking**: Click to earn cookies
- 📈 **Automatic Generation**: Buildings generate cookies per second
- 🛍️ **Upgrade System**: Purchase buildings and enhancements
- 🏆 **Achievements**: Unlock accomplishments
- 💾 **Auto-Save**: Automatic game state persistence

### Buildings & Upgrades
| Building | Base Cost | CPS | Description |
|----------|-----------|-----|-------------|
| Cursor | 15 | 1 | Clicks cookies automatically |
| Grandma | 100 | 5 | Bakes cookies with love |
| Farm | 1,100 | 47 | Grows cookie plants |
| Mine | 12,000 | 260 | Mines cookie ore |
| Factory | 130,000 | 1,400 | Mass cookie production |

### Click Upgrades
- **Better Clicks**: +1 click power (50 cookies)
- **Super Clicks**: +5 click power (500 cookies)
- **Mega Clicks**: +25 click power (5,000 cookies)

## 🛠️ Development

### Prerequisites
- Docker & Docker Compose
- Make (for development commands)
- Git

### Development Commands

```bash
# Environment Management
make setup          # Initialize project
make run            # Start development environment
make stop           # Stop all services
make restart        # Restart services
make clean          # Clean up containers

# Development Tools
make logs           # View all service logs
make logs-go        # View Go app logs
make logs-python    # View Python API logs
make logs-db        # View database logs

# Testing & Quality
make test           # Run all tests
make test-go        # Run Go tests
make test-python    # Run Python tests
make lint           # Run linting
make format         # Format code

# Database Management
make db-migrate     # Run database migrations
make db-reset       # Reset database (⚠️  destructive)
make db-backup      # Create database backup

# Utilities
make shell-go       # Access Go container
make shell-python   # Access Python API container
make shell-db       # Access PostgreSQL
make status         # Check service status
make health         # Health check all services
```

### Service URLs

| Service | URL | Description |
|---------|-----|-------------|
| 🎮 Game Frontend | http://localhost:8080 | Main game interface |
| 🐍 Python API | http://localhost:8001 | Backend API |
| 📖 API Documentation | http://localhost:8001/docs | Swagger UI |
| 📚 API Redoc | http://localhost:8001/redoc | ReDoc UI |
| 🗄️ PostgreSQL | localhost:5432 | Database |
| 🔴 Redis | localhost:6379 | Cache |

## 📂 Project Structure

```
cookie-clicker-game/
├── .github/workflows/     # GitHub Actions CI/CD
├── go-app/               # Go Frontend Application
│   ├── main.go          # Main application
│   ├── templates/       # HTML templates
│   ├── static/          # CSS, JS, images
│   └── Dockerfile       # Go container config
├── python-api/          # Python Backend API
│   ├── main.py         # FastAPI application
│   ├── requirements.txt # Python dependencies
│   └── Dockerfile      # Python container config
├── sql/                # Database scripts
│   └── init.sql        # Database initialization
├── nginx/              # Nginx configuration
│   ├── nginx.conf      # Main nginx config
│   └── conf.d/         # Site configurations
├── docker-compose.yml  # Development environment
├── Makefile           # Development commands
└── README.md          # This file
```

## 🚀 Deployment

### Staging Environment
```bash
make deploy-staging
```

### Production Deployment
```bash
make deploy-prod
```

### Environment Variables

#### Go Application
- `GIN_MODE`: Application mode (debug/release)
- `PYTHON_API_URL`: Python API endpoint
- `PORT`: Server port (default: 8080)

#### Python API
- `DEBUG`: Debug mode (True/False)
- `DATABASE_URL`: PostgreSQL connection string
- `REDIS_URL`: Redis connection string
- `HOST`: Server host (default: 0.0.0.0)
- `PORT`: Server port (default: 8001)

## 🧪 Testing

### Go Tests
```bash
make test-go
# or directly:
docker compose exec go-app go test -v ./...
```

### Python Tests
```bash
make test-python
# or directly:
docker compose exec python-api pytest -v
```

## 📊 Database Schema

### Core Tables
- **users**: User accounts and authentication
- **game_data**: Game state and statistics
- **upgrades**: Available upgrades and buildings
- **user_upgrades**: User-owned upgrades
- **achievements**: Achievement definitions
- **user_achievements**: User achievement progress

### Views
- **leaderboard**: Top players by cookies
- **user_stats**: Comprehensive user statistics

## 🔧 API Endpoints

### Game Data
- `GET /api/v1/game/{user_id}`: Get game data
- `POST /api/v1/game/{user_id}/click`: Process cookie click
- `POST /api/v1/game/{user_id}/upgrade`: Purchase upgrade
- `GET /api/v1/game/{user_id}/save`: Save game state

### Statistics
- `GET /api/v1/stats`: Global game statistics
- `GET /api/v1/leaderboard`: Player leaderboard

## 🏆 Achievements

| Achievement | Requirement | Reward |
|-------------|-------------|--------|
| First Click! | Make 1 click | Recognition |
| Sweet Start | Reach 100 cookies | Milestone |
| Cookie Collector | Reach 1,000 cookies | Milestone |
| Cookie Master | Reach 10,000 cookies | Milestone |
| Cookie Millionaire | Reach 1,000,000 cookies | Prestige |

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 📞 Support

For support, email [your-email] or create an issue in the GitHub repository.

---

**Happy Cookie Clicking!** 🍪🎮