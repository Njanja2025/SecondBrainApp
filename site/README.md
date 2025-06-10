# Second Brain Application

A comprehensive memory and threat management system with real-time monitoring and analytics.

## Features

- Memory analytics and visualization
- Threat monitoring and management
- System health monitoring
- Agent profile management
- Dark/Light mode support
- Mobile-responsive design

## Prerequisites

- Node.js >= 14.0.0
- npm >= 6.0.0
- SQLite3
- PM2 (for remote deployment)

## Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd second-brain
```

2. Install dependencies:
```bash
npm install
```

3. Initialize the database:
```bash
npm run init-db
```

## Development

To start the development server:
```bash
npm run dev
```

The application will be available at `http://localhost:3000`

## Deployment

### Local Deployment

To deploy locally:
```bash
npm run deploy:local
```

### Remote Deployment

1. Update the remote configuration in `config/deployment.json`
2. Deploy to remote server:
```bash
npm run deploy:remote
```

## Configuration

The application can be configured through the `config/deployment.json` file:

```json
{
  "deployment": {
    "remote": {
      "enabled": false,
      "host": "your-server.com",
      "username": "your-username",
      "remote_path": "/path/to/deployment",
      "db_path": "/path/to/database.sqlite",
      "log_path": "/path/to/logs"
    },
    "local": {
      "db_path": "./data/database.sqlite",
      "log_path": "./logs"
    }
  }
}
```

## API Endpoints

### Memory API
- `GET /api/memory/stats` - Get memory statistics
- `GET /api/memory/export` - Export memory data

### Threats API
- `GET /api/threats/stats` - Get threat statistics
- `POST /api/threats/seed-demo` - Seed demo threat data

### Agents API
- `GET /api/agents/:id` - Get agent profile
- `POST /api/agents/:id/sync` - Sync agent

### Health API
- `GET /api/health/status` - Get system health status
- `POST /api/health/logs` - Add system log

## Testing

Run tests:
```bash
npm test
```

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details. 