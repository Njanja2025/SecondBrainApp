import React, { useState, useEffect } from 'react';
import { Bar } from 'react-chartjs-2';
import {
    Chart as ChartJS,
    CategoryScale,
    LinearScale,
    BarElement,
    Title,
    Tooltip,
    Legend
} from 'chart.js';

ChartJS.register(
    CategoryScale,
    LinearScale,
    BarElement,
    Title,
    Tooltip,
    Legend
);

const ThreatStats = () => {
    const [threatData, setThreatData] = useState({
        threats: [],
        status: {
            healthy: 0,
            unhealthy: 0
        },
        lastEntry: null
    });

    const [chartData, setChartData] = useState({
        labels: [],
        datasets: [{
            label: 'Threats by Severity',
            data: [],
            backgroundColor: [
                'rgba(255, 99, 132, 0.5)',
                'rgba(255, 159, 64, 0.5)',
                'rgba(255, 205, 86, 0.5)',
                'rgba(75, 192, 192, 0.5)'
            ]
        }]
    });

    useEffect(() => {
        fetchThreatData();
        const interval = setInterval(fetchThreatData, 10000); // Refresh every 10 seconds
        return () => clearInterval(interval);
    }, []);

    const fetchThreatData = async () => {
        try {
            const response = await fetch('/api/threats/stats');
            const data = await response.json();
            setThreatData(data);
            updateChartData(data);
        } catch (error) {
            console.error('Error fetching threat data:', error);
        }
    };

    const updateChartData = (data) => {
        const threats = data.threats;
        const severityCounts = {
            critical: 0,
            high: 0,
            medium: 0,
            low: 0
        };

        threats.forEach(threat => {
            severityCounts[threat.severity]++;
        });

        setChartData({
            labels: Object.keys(severityCounts),
            datasets: [{
                label: 'Threats by Severity',
                data: Object.values(severityCounts),
                backgroundColor: [
                    'rgba(255, 99, 132, 0.5)',
                    'rgba(255, 159, 64, 0.5)',
                    'rgba(255, 205, 86, 0.5)',
                    'rgba(75, 192, 192, 0.5)'
                ]
            }]
        });
    };

    return (
        <div className="threat-stats">
            <div className="threat-status">
                <h3>System Health</h3>
                <div className="status-indicators">
                    <div className={`status healthy ${threatData.status.healthy > 0 ? 'active' : ''}`}>
                        Healthy: {threatData.status.healthy}
                    </div>
                    <div className={`status unhealthy ${threatData.status.unhealthy > 0 ? 'active' : ''}`}>
                        Unhealthy: {threatData.status.unhealthy}
                    </div>
                </div>
            </div>

            <div className="threat-chart">
                <h3>Threat Distribution</h3>
                <Bar data={chartData} />
            </div>

            <div className="last-threat">
                <h3>Latest Threat</h3>
                {threatData.lastEntry && (
                    <div className="threat-entry">
                        <div className="severity">{threatData.lastEntry.severity}</div>
                        <div className="timestamp">{threatData.lastEntry.timestamp}</div>
                        <div className="description">{threatData.lastEntry.description}</div>
                    </div>
                )}
            </div>

            <div className="threat-table">
                <h3>Active Threats</h3>
                <table>
                    <thead>
                        <tr>
                            <th>Severity</th>
                            <th>Timestamp</th>
                            <th>Description</th>
                            <th>Status</th>
                        </tr>
                    </thead>
                    <tbody>
                        {threatData.threats.map(threat => (
                            <tr key={threat.id} className={`severity-${threat.severity}`}>
                                <td>{threat.severity}</td>
                                <td>{threat.timestamp}</td>
                                <td>{threat.description}</td>
                                <td>{threat.status}</td>
                            </tr>
                        ))}
                    </tbody>
                </table>
            </div>
        </div>
    );
};

export default ThreatStats; 