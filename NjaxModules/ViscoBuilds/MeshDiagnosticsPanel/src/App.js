import React from 'react';
import NodeStatus from './NodeStatus';
import PingTest from './PingTest';

// Njax v1.0 API integration points
// TODO: Import and initialize NjaxIntelligence, NjaxMesh, NjaxWallet APIs here
// Example:
// import { NjaxIntelligence, NjaxMesh, NjaxWallet } from 'njax-sdk';
// const njaxIntelligence = new NjaxIntelligence();
// const njaxMesh = new NjaxMesh();
// const njaxWallet = new NjaxWallet();
// Use these APIs in your components as needed.

export default function App() {
  return (
    <div style={{padding: 24}}>
      <h2>Mesh Diagnostics Panel</h2>
      <NodeStatus />
      <PingTest />
    </div>
  );
}
