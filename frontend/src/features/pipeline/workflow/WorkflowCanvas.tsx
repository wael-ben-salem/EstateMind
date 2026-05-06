import { useCallback, useMemo, useState } from 'react';
import ReactFlow, {
  addEdge,
  Background,
  Connection,
  Controls,
  Edge,
  MiniMap,
  Node,
  OnConnect,
  ReactFlowProvider
} from 'reactflow';
import 'reactflow/dist/style.css';
import { Box } from '@mui/material';

type NodeData = { label: string; kind: 'scraper' | 'validator' | 'transformer' | 'loader' | 'report' };

function kindColor(kind: NodeData['kind']) {
  switch (kind) {
    case 'scraper':
      return '#3b82f6';
    case 'validator':
      return '#10b981';
    case 'transformer':
      return '#f59e0b';
    case 'loader':
      return '#8b5cf6';
    case 'report':
      return '#ef4444';
  }
}

function InnerCanvas() {
  const initialNodes = useMemo<Node<NodeData>[]>(
    () => [
      { id: 'n1', type: 'input', position: { x: 0, y: 80 }, data: { label: 'Scraper (Tayara)', kind: 'scraper' } },
      { id: 'n2', position: { x: 240, y: 80 }, data: { label: 'Validator', kind: 'validator' } },
      { id: 'n3', position: { x: 480, y: 80 }, data: { label: 'Transformer (Spark ETL)', kind: 'transformer' } },
      { id: 'n4', type: 'output', position: { x: 720, y: 80 }, data: { label: 'Loader (Postgres)', kind: 'loader' } }
    ],
    [],
  );

  const initialEdges = useMemo<Edge[]>(
    () => [
      { id: 'e1-2', source: 'n1', target: 'n2', animated: true },
      { id: 'e2-3', source: 'n2', target: 'n3', animated: true },
      { id: 'e3-4', source: 'n3', target: 'n4', animated: true }
    ],
    [],
  );

  const [nodes, setNodes] = useState<Node<NodeData>[]>(initialNodes);
  const [edges, setEdges] = useState<Edge[]>(initialEdges);

  const onConnect: OnConnect = useCallback(
    (connection: Connection) => setEdges((eds) => addEdge({ ...connection, animated: true }, eds)),
    [],
  );

  return (
    <Box sx={{ height: 520, borderRadius: 2, overflow: 'hidden', border: '1px solid', borderColor: 'divider' }}>
      <ReactFlow
        nodes={nodes}
        edges={edges}
        onNodesChange={setNodes as any}
        onEdgesChange={setEdges as any}
        onConnect={onConnect}
        fitView
      >
        <MiniMap
          nodeColor={(n) => kindColor((n.data as NodeData).kind)}
          nodeStrokeWidth={3}
          zoomable
          pannable
        />
        <Controls />
        <Background gap={16} />
      </ReactFlow>
    </Box>
  );
}

export function WorkflowCanvas() {
  return (
    <ReactFlowProvider>
      <InnerCanvas />
    </ReactFlowProvider>
  );
}

