const express = require('express');
const router = express.Router();
const sqlite3 = require('sqlite3').verbose();
const path = require('path');

// Database connection based on deployment
const getDbPath = () => {
    const config = require('../config/deployment.json');
    return config.deployment.remote.enabled 
        ? config.deployment.remote.db_path 
        : config.deployment.local.db_path;
};

// Initialize database connection
const db = new sqlite3.Database(getDbPath());

// Get threat statistics
router.get('/stats', async (req, res) => {
    try {
        const threats = await new Promise((resolve, reject) => {
            db.all(`
                SELECT *
                FROM threats
                WHERE status = 'active'
                ORDER BY severity DESC, timestamp DESC
            `, (err, rows) => {
                if (err) reject(err);
                resolve(rows);
            });
        });

        const status = await new Promise((resolve, reject) => {
            db.all(`
                SELECT 
                    CASE 
                        WHEN COUNT(*) = 0 THEN 'healthy'
                        WHEN COUNT(*) > 0 AND MAX(severity) <= 'medium' THEN 'warning'
                        ELSE 'unhealthy'
                    END as status,
                    COUNT(*) as total,
                    SUM(CASE WHEN severity = 'critical' THEN 1 ELSE 0 END) as critical,
                    SUM(CASE WHEN severity = 'high' THEN 1 ELSE 0 END) as high,
                    SUM(CASE WHEN severity = 'medium' THEN 1 ELSE 0 END) as medium,
                    SUM(CASE WHEN severity = 'low' THEN 1 ELSE 0 END) as low
                FROM threats
                WHERE status = 'active'
            `, (err, rows) => {
                if (err) reject(err);
                resolve(rows[0]);
            });
        });

        const lastEntry = await new Promise((resolve, reject) => {
            db.get(`
                SELECT *
                FROM threats
                ORDER BY timestamp DESC
                LIMIT 1
            `, (err, row) => {
                if (err) reject(err);
                resolve(row);
            });
        });

        res.json({
            threats,
            status: {
                healthy: status.status === 'healthy' ? 1 : 0,
                unhealthy: status.status === 'unhealthy' ? 1 : 0
            },
            lastEntry
        });
    } catch (error) {
        console.error('Error fetching threat stats:', error);
        res.status(500).json({ error: 'Failed to fetch threat statistics' });
    }
});

// Seed demo threat data
router.post('/seed-demo', async (req, res) => {
    try {
        const demoThreats = [
            {
                severity: 'critical',
                description: 'Unauthorized access attempt detected',
                timestamp: new Date().toISOString(),
                status: 'active'
            },
            {
                severity: 'high',
                description: 'Suspicious network activity',
                timestamp: new Date().toISOString(),
                status: 'active'
            },
            {
                severity: 'medium',
                description: 'Unusual memory usage pattern',
                timestamp: new Date().toISOString(),
                status: 'active'
            },
            {
                severity: 'low',
                description: 'Non-critical system warning',
                timestamp: new Date().toISOString(),
                status: 'active'
            }
        ];

        await new Promise((resolve, reject) => {
            db.run('DELETE FROM threats WHERE status = "demo"', (err) => {
                if (err) reject(err);
                resolve();
            });
        });

        const stmt = db.prepare(`
            INSERT INTO threats (severity, description, timestamp, status)
            VALUES (?, ?, ?, ?)
        `);

        for (const threat of demoThreats) {
            await new Promise((resolve, reject) => {
                stmt.run(
                    threat.severity,
                    threat.description,
                    threat.timestamp,
                    'demo',
                    (err) => {
                        if (err) reject(err);
                        resolve();
                    }
                );
            });
        }

        stmt.finalize();
        res.json({ message: 'Demo threat data seeded successfully' });
    } catch (error) {
        console.error('Error seeding demo threat data:', error);
        res.status(500).json({ error: 'Failed to seed demo threat data' });
    }
});

module.exports = router; 