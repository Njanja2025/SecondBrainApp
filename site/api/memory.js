const express = require('express');
const router = express.Router();
const sqlite3 = require('sqlite3').verbose();
const path = require('path');
const fs = require('fs');

// Database connection based on deployment
const getDbPath = () => {
    const config = require('../config/deployment.json');
    return config.deployment.remote.enabled 
        ? config.deployment.remote.db_path 
        : config.deployment.local.db_path;
};

// Initialize database connection
const db = new sqlite3.Database(getDbPath());

// Get memory statistics
router.get('/stats', async (req, res) => {
    try {
        const stats = await new Promise((resolve, reject) => {
            db.all(`
                SELECT 
                    strftime('%Y-%m-%d', timestamp) as date,
                    COUNT(*) as count
                FROM memory_entries
                GROUP BY date
                ORDER BY date DESC
                LIMIT 30
            `, (err, rows) => {
                if (err) reject(err);
                resolve(rows);
            });
        });

        const topAgents = await new Promise((resolve, reject) => {
            db.all(`
                SELECT 
                    agent_id,
                    agent_name,
                    COUNT(*) as entries
                FROM memory_entries
                GROUP BY agent_id
                ORDER BY entries DESC
                LIMIT 5
            `, (err, rows) => {
                if (err) reject(err);
                resolve(rows);
            });
        });

        const lastEntries = await new Promise((resolve, reject) => {
            db.all(`
                SELECT *
                FROM memory_entries
                ORDER BY timestamp DESC
                LIMIT 5
            `, (err, rows) => {
                if (err) reject(err);
                resolve(rows);
            });
        });

        res.json({
            entries: stats,
            topAgents,
            lastEntries
        });
    } catch (error) {
        console.error('Error fetching memory stats:', error);
        res.status(500).json({ error: 'Failed to fetch memory statistics' });
    }
});

// Export memory data
router.get('/export', async (req, res) => {
    try {
        const format = req.query.format || 'json';
        const data = await new Promise((resolve, reject) => {
            db.all('SELECT * FROM memory_entries ORDER BY timestamp DESC', (err, rows) => {
                if (err) reject(err);
                resolve(rows);
            });
        });

        if (format === 'csv') {
            const csv = convertToCSV(data);
            res.setHeader('Content-Type', 'text/csv');
            res.setHeader('Content-Disposition', 'attachment; filename=memory_export.csv');
            res.send(csv);
        } else {
            res.json(data);
        }
    } catch (error) {
        console.error('Error exporting memory data:', error);
        res.status(500).json({ error: 'Failed to export memory data' });
    }
});

// Helper function to convert data to CSV
function convertToCSV(data) {
    const headers = Object.keys(data[0]);
    const csvRows = [
        headers.join(','),
        ...data.map(row => 
            headers.map(header => 
                JSON.stringify(row[header])
            ).join(',')
        )
    ];
    return csvRows.join('\n');
}

module.exports = router; 