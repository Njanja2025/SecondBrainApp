import React, { useState } from 'react';

export default function NodeStatus() {
  const [nodes] = useState([
    { id: 'Node-1', status: 'online' },
    { id: 'Node-2', status: 'offline' },
    { id: 'Node-3', status: 'online' },
  ]);
  return (
    <table style={{width: '100%', marginBottom: 16}}>
      <thead>
        <tr>
          <th>Node</th>
          <th>Status</th>
        </tr>
      </thead>
      <tbody>
        {nodes.map(node => (
          <tr key={node.id} style={{background: node.status === 'online' ? '#e0ffe0' : '#ffe0e0'}}>
            <td>{node.id}</td>
            <td>{node.status}</td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}
