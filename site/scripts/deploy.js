const { execSync } = require('child_process');
const fs = require('fs');
const path = require('path');
const config = require('../config/deployment.json');

// Function to run shell commands
const runCommand = (command) => {
    try {
        execSync(command, { stdio: 'inherit' });
    } catch (error) {
        console.error(`Failed to execute command: ${command}`);
        process.exit(1);
    }
};

// Function to ensure directory exists
const ensureDirectoryExists = (dirPath) => {
    if (!fs.existsSync(dirPath)) {
        fs.mkdirSync(dirPath, { recursive: true });
    }
};

// Function to deploy to local environment
const deployLocal = () => {
    console.log('Deploying to local environment...');
    
    // Ensure local directories exist
    ensureDirectoryExists(config.deployment.local.db_path);
    ensureDirectoryExists(config.deployment.local.log_path);
    
    // Install dependencies
    runCommand('npm install');
    
    // Initialize database
    runCommand('node db/init.js');
    
    // Start server
    runCommand('node server.js');
};

// Function to deploy to remote environment
const deployRemote = () => {
    console.log('Deploying to remote environment...');
    
    const { host, username, remote_path } = config.deployment.remote;
    
    // Create remote directories
    runCommand(`ssh ${username}@${host} "mkdir -p ${remote_path}"`);
    
    // Copy files to remote server
    runCommand(`rsync -avz --exclude 'node_modules' --exclude '.git' ./ ${username}@${host}:${remote_path}`);
    
    // Install dependencies and start server on remote
    runCommand(`ssh ${username}@${host} "cd ${remote_path} && npm install && node db/init.js && pm2 start server.js --name second-brain"`);
};

// Main deployment function
const deploy = () => {
    const isRemote = process.argv.includes('--remote');
    
    if (isRemote) {
        deployRemote();
    } else {
        deployLocal();
    }
};

// Run deployment
deploy(); 