import React, { useState, useEffect } from 'react';

const SystemHealth = () => {
    const [healthData, setHealthData] = useState({
        status: 'healthy',
        components: {
            memory: { status: 'healthy', message: '' },
            threats: { status: 'healthy', message: '' },
            agents: { status: 'healthy', message: '' }
        },
        logs: []
    });

    useEffect(() => {
        fetchHealthData();
        const interval = setInterval(fetchHealthData, 10000); // Refresh every 10 seconds
        return () => clearInterval(interval);
    }, []);

    const fetchHealthData = async () => {
        try {
            const response = await fetch('/api/health');
            const data = await response.json();
            setHealthData(data);
        } catch (error) {
            console.error('Error fetching health data:', error);
        }
    };

    const getStatusClass = (status) => {
        return `status-${status.toLowerCase()}`;
    };

    return (
        <div className="system-health">
            <div className="health-header">
                <h2>System Health</h2>
                <div className={`overall-status ${getStatusClass(healthData.status)}`}>
                    {healthData.status}
                </div>
            </div>

            <div className="component-status">
                <h3>Component Status</h3>
                <div className="components">
                    {Object.entries(healthData.components).map(([component, data]) => (
                        <div 
                            key={component}
                            className={`component ${getStatusClass(data.status)} ${data.status !== 'healthy' ? 'blink' : ''}`}
                        >
                            <span className="component-name">{component}</span>
                            <span className="component-status">{data.status}</span>
                            {data.message && (
                                <span className="component-message">{data.message}</span>
                            )}
                        </div>
                    ))}
                </div>
            </div>

            <div className="system-logs">
                <h3>Recent Logs</h3>
                <div className="logs-container">
                    {healthData.logs.map((log, index) => (
                        <div key={index} className={`log-entry ${getStatusClass(log.level)}`}>
                            <span className="log-timestamp">{log.timestamp}</span>
                            <span className="log-level">{log.level}</span>
                            <span className="log-message">{log.message}</span>
                        </div>
                    ))}
                </div>
            </div>

            <div className="health-actions">
                <button onClick={fetchHealthData}>Refresh</button>
                <button onClick={() => setHealthData(prev => ({ ...prev, showLogs: !prev.showLogs }))}>
                    {healthData.showLogs ? 'Hide Logs' : 'Show Logs'}
                </button>
            </div>
        </div>
    );
};

export default SystemHealth; 