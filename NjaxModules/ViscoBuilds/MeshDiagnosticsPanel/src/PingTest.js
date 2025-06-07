import React, { useState } from 'react';

export default function PingTest() {
  const [log, setLog] = useState([]);
  const pingNode = (nodeId) => {
    setLog(l => [...l, `Pinged ${nodeId}: ${Math.floor(Math.random()*50)}ms`]);
  };
  return (
    <div>
      <h3>Ping Test</h3>
      <button onClick={() => pingNode('Node-1')}>Ping Node-1</button>
      <button onClick={() => pingNode('Node-2')} style={{marginLeft: 8}}>Ping Node-2</button>
      <button onClick={() => pingNode('Node-3')} style={{marginLeft: 8}}>Ping Node-3</button>
      <div style={{background: '#f9f9f9', padding: 12, minHeight: 40, maxHeight: 120, overflowY: 'auto', marginTop: 8}}>
        {log.map((entry, i) => <div key={i}>{entry}</div>)}
      </div>
    </div>
  );
}
