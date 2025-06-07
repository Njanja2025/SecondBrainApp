import React, { useEffect, useState } from 'react';

// Dummy Mesh API hooks (replace with real API calls)
const useMeshNodes = () => {
  const [nodes, setNodes] = useState([
    { id: 'Node-1', status: 'online', latency: 12 },
    { id: 'Node-2', status: 'offline', latency: null },
    { id: 'Node-3', status: 'online', latency: 20 },
  ]);
  return [nodes, setNodes];
};

export default function DiagnosticsPanel() {
  const [nodes, setNodes] = useMeshNodes();
  const [log, setLog] = useState([]);

  const pingNode = (nodeId) => {
    // Simulate ping
    setLog(l => [...l, `Pinged ${nodeId}: ${Math.floor(Math.random()*50)}ms`]);
  };

  const restartNode = (nodeId) => {
    // Simulate restart
    setLog(l => [...l, `Restarted ${nodeId}`]);
  };

  useEffect(() => {
    // Simulate auto-log error reports
    const interval = setInterval(() => {
      setLog(l => [...l, `Auto-log: All nodes checked at ${new Date().toLocaleTimeString()}`]);
    }, 10000);
    return () => clearInterval(interval);
  }, []);

  return (
    <div style={{padding: 24}}>
      <h2>NjaxMesh Node Diagnostics</h2>
      <table style={{width: '100%', marginBottom: 16}}>
        <thead>
          <tr>
            <th>Node</th>
            <th>Status</th>
            <th>Latency</th>
            <th>Actions</th>
          </tr>
        </thead>
        <tbody>
          {nodes.map(node => (
            <tr key={node.id} style={{background: node.status === 'online' ? '#e0ffe0' : '#ffe0e0'}}>
              <td>{node.id}</td>
              <td>{node.status}</td>
              <td>{node.latency !== null ? `${node.latency} ms` : 'N/A'}</td>
              <td>
                <button onClick={() => pingNode(node.id)}>Ping</button>
                <button onClick={() => restartNode(node.id)} style={{marginLeft: 8}}>Restart</button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
      <h3>Event Log</h3>
      <div style={{background: '#f9f9f9', padding: 12, minHeight: 80, maxHeight: 200, overflowY: 'auto'}}>
        {log.map((entry, i) => <div key={i}>{entry}</div>)}
      </div>
    </div>
  );
}
