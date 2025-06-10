const express = require('express');
const path = require('path');
const cors = require('cors');
const bodyParser = require('body-parser');
const config = require('./config/deployment.json');

// Import routes
const memoryRoutes = require('./api/memory');
const threatRoutes = require('./api/threats');
const agentRoutes = require('./api/agents');
const healthRoutes = require('./api/health');

const app = express();
const port = process.env.PORT || 3000;

// Middleware
app.use(cors());
app.use(bodyParser.json());
app.use(express.static(path.join(__dirname, 'public')));

// API Routes
app.use('/api/memory', memoryRoutes);
app.use('/api/threats', threatRoutes);
app.use('/api/agents', agentRoutes);
app.use('/api/health', healthRoutes);

// Serve index.html for all routes (SPA)
app.get('*', (req, res) => {
    res.sendFile(path.join(__dirname, 'public', 'index.html'));
});

// Error handling middleware
app.use((err, req, res, next) => {
    console.error(err.stack);
    res.status(500).json({ error: 'Something went wrong!' });
});

// Start server
app.listen(port, () => {
    console.log(`Server running on port ${port}`);
    console.log(`Deployment mode: ${config.deployment.remote.enabled ? 'Remote' : 'Local'}`);
}); 