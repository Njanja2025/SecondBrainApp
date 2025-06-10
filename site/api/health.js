const express = require('express');
const router = express.Router();
const sqlite3 = require('sqlite3').verbose();
const path = require('path');
const os = require('os');

// Database connection based on deployment
const getDbPath = () => {
    const config = require('../config/deployment.json');
    return config.deployment.remote.enabled 
        ? config.deployment.remote.db_path 
        : config.deployment.local.db_path;
};

// Initialize database connection
const db = new sqlite3.Database(getDbPath());

// Get system health status
router.get('/status', async (req, res) => {
    try {
        // Get database status
        const dbStatus = await new Promise((resolve, reject) => {
            db.get('SELECT 1', (err) => {
                if (err) {
                    resolve({ status: 'error', message: err.message });
                } else {
                    resolve({ status: 'healthy', message: 'Database connection is active' });
                }
            });
        });

        // Get system metrics
        const systemMetrics = {
            cpu: {
                usage: os.loadavg()[0],
                cores: os.cpus().length
            },
            memory: {
                total: os.totalmem(),
                free: os.freemem(),
                usage: ((os.totalmem() - os.freemem()) / os.totalmem()) * 100
            },
            uptime: os.uptime()
        };

        // Get component statuses
        const components = [
            {
                name: 'Database',
                status: dbStatus.status,
                message: dbStatus.message
            },
            {
                name: 'Memory Layer',
                status: 'healthy',
                message: 'Memory layer is operational'
            },
            {
                name: 'Threat Engine',
                status: 'healthy',
                message: 'Threat engine is running'
            }
        ];

        // Get recent logs
        const logs = await new Promise((resolve, reject) => {
            db.all(`
                SELECT *
                FROM system_logs
                ORDER BY timestamp DESC
                LIMIT 10
            `, (err, rows) => {
                if (err) reject(err);
                resolve(rows);
            });
        });

        // Calculate overall status
        const overallStatus = components.every(c => c.status === 'healthy')
            ? 'healthy'
            : components.some(c => c.status === 'error')
                ? 'error'
                : 'warning';

        res.json({
            status: overallStatus,
            components,
            metrics: systemMetrics,
            logs
        });
    } catch (error) {
        console.error('Error fetching system health:', error);
        res.status(500).json({ error: 'Failed to fetch system health status' });
    }
});

// Add system log
router.post('/logs', async (req, res) => {
    try {
        const { level, message } = req.body;
        
        await new Promise((resolve, reject) => {
            db.run(`
                INSERT INTO system_logs (level, message, timestamp)
                VALUES (?, ?, CURRENT_TIMESTAMP)
            `, [level, message], (err) => {
                if (err) reject(err);
                resolve();
            });
        });

        res.json({ message: 'Log entry added successfully' });
    } catch (error) {
        console.error('Error adding system log:', error);
        res.status(500).json({ error: 'Failed to add system log' });
    }
});

module.exports = router; 