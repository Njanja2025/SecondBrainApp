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

// Get agent profile
router.get('/:id', async (req, res) => {
    try {
        const agent = await new Promise((resolve, reject) => {
            db.get(`
                SELECT *
                FROM agents
                WHERE id = ?
            `, [req.params.id], (err, row) => {
                if (err) reject(err);
                resolve(row);
            });
        });

        if (!agent) {
            return res.status(404).json({ error: 'Agent not found' });
        }

        const metrics = await new Promise((resolve, reject) => {
            db.get(`
                SELECT 
                    COUNT(*) as memoryEntries,
                    SUM(CASE WHEN type = 'threat' THEN 1 ELSE 0 END) as threatsDetected,
                    MAX(timestamp) as lastActive
                FROM memory_entries
                WHERE agent_id = ?
            `, [req.params.id], (err, row) => {
                if (err) reject(err);
                resolve(row);
            });
        });

        res.json({
            ...agent,
            metrics
        });
    } catch (error) {
        console.error('Error fetching agent profile:', error);
        res.status(500).json({ error: 'Failed to fetch agent profile' });
    }
});

// Sync agent
router.post('/:id/sync', async (req, res) => {
    try {
        const agent = await new Promise((resolve, reject) => {
            db.get(`
                SELECT *
                FROM agents
                WHERE id = ?
            `, [req.params.id], (err, row) => {
                if (err) reject(err);
                resolve(row);
            });
        });

        if (!agent) {
            return res.status(404).json({ error: 'Agent not found' });
        }

        // Update agent status and last sync time
        await new Promise((resolve, reject) => {
            db.run(`
                UPDATE agents
                SET 
                    status = 'syncing',
                    last_sync = CURRENT_TIMESTAMP
                WHERE id = ?
            `, [req.params.id], (err) => {
                if (err) reject(err);
                resolve();
            });
        });

        // Simulate sync process
        setTimeout(async () => {
            try {
                await new Promise((resolve, reject) => {
                    db.run(`
                        UPDATE agents
                        SET status = 'active'
                        WHERE id = ?
                    `, [req.params.id], (err) => {
                        if (err) reject(err);
                        resolve();
                    });
                });

                // Fetch updated agent data
                const updatedAgent = await new Promise((resolve, reject) => {
                    db.get(`
                        SELECT *
                        FROM agents
                        WHERE id = ?
                    `, [req.params.id], (err, row) => {
                        if (err) reject(err);
                        resolve(row);
                    });
                });

                res.json(updatedAgent);
            } catch (error) {
                console.error('Error completing agent sync:', error);
                res.status(500).json({ error: 'Failed to complete agent sync' });
            }
        }, 2000); // Simulate 2-second sync process
    } catch (error) {
        console.error('Error starting agent sync:', error);
        res.status(500).json({ error: 'Failed to start agent sync' });
    }
});

module.exports = router; 