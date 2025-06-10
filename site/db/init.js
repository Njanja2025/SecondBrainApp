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

// Ensure database directory exists
const dbPath = getDbPath();
const dbDir = path.dirname(dbPath);
if (!fs.existsSync(dbDir)) {
    fs.mkdirSync(dbDir, { recursive: true });
}

// Initialize database connection
const db = new sqlite3.Database(dbPath);

// Create tables
const initDatabase = async () => {
    try {
        // Create agents table
        await new Promise((resolve, reject) => {
            db.run(`
                CREATE TABLE IF NOT EXISTS agents (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    type TEXT NOT NULL,
                    status TEXT DEFAULT 'active',
                    last_sync TIMESTAMP,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            `, (err) => {
                if (err) reject(err);
                resolve();
            });
        });

        // Create memory_entries table
        await new Promise((resolve, reject) => {
            db.run(`
                CREATE TABLE IF NOT EXISTS memory_entries (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    agent_id TEXT NOT NULL,
                    agent_name TEXT NOT NULL,
                    content TEXT NOT NULL,
                    type TEXT NOT NULL,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (agent_id) REFERENCES agents(id)
                )
            `, (err) => {
                if (err) reject(err);
                resolve();
            });
        });

        // Create threats table
        await new Promise((resolve, reject) => {
            db.run(`
                CREATE TABLE IF NOT EXISTS threats (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    severity TEXT NOT NULL,
                    description TEXT NOT NULL,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    status TEXT DEFAULT 'active'
                )
            `, (err) => {
                if (err) reject(err);
                resolve();
            });
        });

        // Create system_logs table
        await new Promise((resolve, reject) => {
            db.run(`
                CREATE TABLE IF NOT EXISTS system_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    level TEXT NOT NULL,
                    message TEXT NOT NULL,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            `, (err) => {
                if (err) reject(err);
                resolve();
            });
        });

        console.log('Database initialized successfully');
    } catch (error) {
        console.error('Error initializing database:', error);
        throw error;
    }
};

// Seed demo data
const seedDemoData = async () => {
    try {
        // Seed agents
        const agents = [
            { id: 'agent1', name: 'Memory Agent', type: 'memory' },
            { id: 'agent2', name: 'Threat Agent', type: 'threat' },
            { id: 'agent3', name: 'System Agent', type: 'system' }
        ];

        for (const agent of agents) {
            await new Promise((resolve, reject) => {
                db.run(`
                    INSERT OR IGNORE INTO agents (id, name, type)
                    VALUES (?, ?, ?)
                `, [agent.id, agent.name, agent.type], (err) => {
                    if (err) reject(err);
                    resolve();
                });
            });
        }

        // Seed memory entries
        const memoryEntries = [
            { agent_id: 'agent1', agent_name: 'Memory Agent', content: 'System check completed', type: 'info' },
            { agent_id: 'agent1', agent_name: 'Memory Agent', content: 'Memory optimization needed', type: 'warning' },
            { agent_id: 'agent2', agent_name: 'Threat Agent', content: 'Threat scan completed', type: 'info' }
        ];

        for (const entry of memoryEntries) {
            await new Promise((resolve, reject) => {
                db.run(`
                    INSERT INTO memory_entries (agent_id, agent_name, content, type)
                    VALUES (?, ?, ?, ?)
                `, [entry.agent_id, entry.agent_name, entry.content, entry.type], (err) => {
                    if (err) reject(err);
                    resolve();
                });
            });
        }

        // Seed system logs
        const logs = [
            { level: 'info', message: 'System initialized' },
            { level: 'warning', message: 'High memory usage detected' },
            { level: 'error', message: 'Database connection timeout' }
        ];

        for (const log of logs) {
            await new Promise((resolve, reject) => {
                db.run(`
                    INSERT INTO system_logs (level, message)
                    VALUES (?, ?)
                `, [log.level, log.message], (err) => {
                    if (err) reject(err);
                    resolve();
                });
            });
        }

        console.log('Demo data seeded successfully');
    } catch (error) {
        console.error('Error seeding demo data:', error);
        throw error;
    }
};

// Initialize database and seed demo data
const initialize = async () => {
    try {
        await initDatabase();
        await seedDemoData();
        db.close();
    } catch (error) {
        console.error('Initialization failed:', error);
        process.exit(1);
    }
};

initialize(); 