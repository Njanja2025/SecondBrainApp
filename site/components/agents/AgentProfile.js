import React, { useState, useEffect } from 'react';

const AgentProfile = ({ agentId, onClose }) => {
    const [agent, setAgent] = useState(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);

    useEffect(() => {
        fetchAgentData();
    }, [agentId]);

    const fetchAgentData = async () => {
        try {
            setLoading(true);
            const response = await fetch(`/api/agents/${agentId}`);
            const data = await response.json();
            setAgent(data);
            setError(null);
        } catch (error) {
            setError('Failed to load agent data');
            console.error('Error fetching agent data:', error);
        } finally {
            setLoading(false);
        }
    };

    const handleSync = async () => {
        try {
            setLoading(true);
            const response = await fetch(`/api/agents/${agentId}/sync`, {
                method: 'POST'
            });
            const data = await response.json();
            setAgent(data);
            setError(null);
        } catch (error) {
            setError('Failed to sync agent');
            console.error('Error syncing agent:', error);
        } finally {
            setLoading(false);
        }
    };

    if (loading) {
        return (
            <div className="agent-profile loading">
                <div className="loading-spinner"></div>
                <p>Loading agent data...</p>
            </div>
        );
    }

    if (error) {
        return (
            <div className="agent-profile error">
                <p className="error-message">{error}</p>
                <button onClick={fetchAgentData}>Retry</button>
            </div>
        );
    }

    if (!agent) {
        return (
            <div className="agent-profile error">
                <p>Agent not found</p>
                <button onClick={onClose}>Close</button>
            </div>
        );
    }

    return (
        <div className="agent-profile">
            <div className="profile-header">
                <h2>{agent.name}</h2>
                <button className="close-button" onClick={onClose}>×</button>
            </div>

            <div className="profile-content">
                <div className="agent-status">
                    <h3>Status</h3>
                    <div className={`status-indicator ${agent.status}`}>
                        {agent.status}
                    </div>
                </div>

                <div className="agent-metrics">
                    <h3>Metrics</h3>
                    <div className="metric">
                        <span className="label">Memory Entries:</span>
                        <span className="value">{agent.metrics.memoryEntries}</span>
                    </div>
                    <div className="metric">
                        <span className="label">Threats Detected:</span>
                        <span className="value">{agent.metrics.threatsDetected}</span>
                    </div>
                    <div className="metric">
                        <span className="label">Last Active:</span>
                        <span className="value">{agent.metrics.lastActive}</span>
                    </div>
                </div>

                <div className="agent-config">
                    <h3>Configuration</h3>
                    <pre>{JSON.stringify(agent.config, null, 2)}</pre>
                </div>

                <div className="agent-actions">
                    <button 
                        className="sync-button"
                        onClick={handleSync}
                        disabled={loading}
                    >
                        {loading ? 'Syncing...' : 'Sync Agent'}
                    </button>
                </div>
            </div>
        </div>
    );
};

export default AgentProfile; 