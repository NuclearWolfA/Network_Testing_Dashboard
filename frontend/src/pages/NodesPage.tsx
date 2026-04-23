import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";

import { fetchNodes } from "../api";
import type { NodeRecord } from "../types";

export default function NodesPage() {
  const [nodes, setNodes] = useState<NodeRecord[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const navigate = useNavigate();

  const loadNodes = async () => {
    setIsLoading(true);
    setError(null);
    try {
      const data = await fetchNodes();
      setNodes(data);
    } catch (err) {
      const message = err instanceof Error ? err.message : "Failed to fetch nodes";
      setError(message);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    void loadNodes();
  }, []);

  const goToMessageQueryPage = () => {
    navigate("/messages/query");
  };

  return (
    <main className="page">
      <section className="panel">
        <p className="eyebrow">Network Testing Dashboard</p>
        <div className="panel-head">
          <h1>Nodes</h1>
          <div className="actions-row">
            <button type="button" onClick={goToMessageQueryPage}>Message Query</button>
            <button type="button" onClick={() => void loadNodes()} disabled={isLoading}>
              {isLoading ? "Loading..." : "Refresh"}
            </button>
          </div>
        </div>

        {error ? <p className="error">{error}</p> : null}

        <div className="table-wrap">
          <table>
            <thead>
              <tr>
                <th>Node ID</th>
                <th>Backend ID</th>
                <th>Last Byte</th>
              </tr>
            </thead>
            <tbody>
              {!isLoading && nodes.length === 0 ? (
                <tr>
                  <td colSpan={3} className="empty">No nodes found in database.</td>
                </tr>
              ) : (
                nodes.map((node) => (
                  <tr key={`${node.node_id}-${node.backend_id}`}>
                    <td>{node.node_id}</td>
                    <td>{node.backend_id}</td>
                    <td>{node.last_byte}</td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </section>
    </main>
  );
}
