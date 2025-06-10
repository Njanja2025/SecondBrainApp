import React, { useState, useEffect } from 'react';
import { Line } from 'react-chartjs-2';
import {
    Chart as ChartJS,
    CategoryScale,
    LinearScale,
    PointElement,
    LineElement,
    Title,
    Tooltip,
    Legend
} from 'chart.js';

ChartJS.register(
    CategoryScale,
    LinearScale,
    PointElement,
    LineElement,
    Title,
    Tooltip,
    Legend
);

const MemoryStats = () => {
    const [memoryData, setMemoryData] = useState({
        entries: [],
        topAgents: [],
        lastEntries: []
    });

    const [chartData, setChartData] = useState({
        labels: [],
        datasets: [{
            label: 'Memory Entries',
            data: [],
            borderColor: 'rgb(75, 192, 192)',
            tension: 0.1
        }]
    });

    useEffect(() => {
        fetchMemoryData();
        const interval = setInterval(fetchMemoryData, 10000); // Refresh every 10 seconds
        return () => clearInterval(interval);
    }, []);

    const fetchMemoryData = async () => {
        try {
            const response = await fetch('/api/memory/stats');
            const data = await response.json();
            setMemoryData(data);
            updateChartData(data);
        } catch (error) {
            console.error('Error fetching memory data:', error);
        }
    };

    const updateChartData = (data) => {
        const entries = data.entries;
        setChartData({
            labels: entries.map(entry => entry.timestamp),
            datasets: [{
                label: 'Memory Entries',
                data: entries.map(entry => entry.count),
                borderColor: 'rgb(75, 192, 192)',
                tension: 0.1
            }]
        });
    };

    const exportMemory = async (format) => {
        try {
            const response = await fetch(`/api/memory/export?format=${format}`);
            const blob = await response.blob();
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `memory_export.${format}`;
            document.body.appendChild(a);
            a.click();
            window.URL.revokeObjectURL(url);
            document.body.removeChild(a);
        } catch (error) {
            console.error('Error exporting memory:', error);
        }
    };

    return (
        <div className="memory-stats">
            <div className="memory-chart">
                <h3>Memory Entries Over Time</h3>
                <Line data={chartData} />
            </div>

            <div className="top-agents">
                <h3>Top Memory Contributors</h3>
                <ul>
                    {memoryData.topAgents.map(agent => (
                        <li key={agent.id}>
                            {agent.name}: {agent.entries} entries
                        </li>
                    ))}
                </ul>
            </div>

            <div className="last-entries">
                <h3>Recent Memory Entries</h3>
                <ul>
                    {memoryData.lastEntries.map(entry => (
                        <li key={entry.id}>
                            <span className="timestamp">{entry.timestamp}</span>
                            <span className="content">{entry.content}</span>
                        </li>
                    ))}
                </ul>
            </div>

            <div className="export-buttons">
                <button onClick={() => exportMemory('csv')}>Export as CSV</button>
                <button onClick={() => exportMemory('json')}>Export as JSON</button>
            </div>
        </div>
    );
};

export default MemoryStats; 