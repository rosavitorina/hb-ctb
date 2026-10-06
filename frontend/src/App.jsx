import { Background, Controls, ReactFlow } from "@xyflow/react";
import "@xyflow/react/dist/style.css";
import "./App.css";

const nodes = [
  { id: "start", position: { x: 0, y: 100 }, data: { label: "Run mongo.py" } },
  { id: "config", position: { x: 200, y: 100 }, data: { label: "Load .env\nRead MONGO_URI" } },
  { id: "client", position: { x: 430, y: 100 }, data: { label: "FMPClient.get_quote('AAPL')" } },
  { id: "api", position: { x: 700, y: 100 }, data: { label: "FMP API" } },
  { id: "save", position: { x: 930, y: 100 }, data: { label: "Save quote in MongoDB" } },
];

const edges = [
  { id: "e1", source: "start", target: "config", animated: true },
  { id: "e2", source: "config", target: "client", animated: true },
  { id: "e3", source: "client", target: "api", animated: true },
  { id: "e4", source: "api", target: "save", label: "quote response", animated: true },
];

export default function App() {
  return (
    <main className="flow-page">
      <h1>HB-CTB: Current Data Flow</h1>
      <div className="flow-canvas">
        <ReactFlow nodes={nodes} edges={edges} fitView>
          <Background />
          <Controls />
        </ReactFlow>
      </div>
    </main>
  );
}