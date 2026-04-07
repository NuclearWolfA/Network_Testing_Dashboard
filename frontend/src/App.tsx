import { FormEvent, useEffect, useState } from "react";

import { getDuplicates, getMetrics, getNodeStats, getPacketPath, getRecentMessages, searchPackets } from "./api";
import { DuplicatePacket, LogicalPacket, Metrics, NodeStat, PacketPath, RecentMessage } from "./types";

function formatDate(value: string | null | undefined): string {
  if (!value) return "-";
  return new Date(value).toLocaleString();
}

export default function App() {
  const [metrics, setMetrics] = useState<Metrics | null>(null);
  const [nodes, setNodes] = useState<NodeStat[]>([]);
  const [messages, setMessages] = useState<RecentMessage[]>([]);
  const [duplicates, setDuplicates] = useState<DuplicatePacket[]>([]);
  const [packets, setPackets] = useState<LogicalPacket[]>([]);
  const [pathData, setPathData] = useState<PacketPath | null>(null);
  const [error, setError] = useState<string | null>(null);

  const [fromNode, setFromNode] = useState("");
  const [toNode, setToNode] = useState("");
  const [packetType, setPacketType] = useState("");

  async function loadDashboard() {
    try {
      setError(null);
      const [m, n, recent, dups] = await Promise.all([getMetrics(), getNodeStats(), getRecentMessages(), getDuplicates()]);
      setMetrics(m);
      setNodes(n);
      setMessages(recent);
      setDuplicates(dups);
    } catch (err) {
      setError((err as Error).message);
    }
  }

  useEffect(() => {
    void loadDashboard();
  }, []);

  async function onSearch(event: FormEvent) {
    event.preventDefault();
    try {
      setError(null);
      const results = await searchPackets({
        fromNode: fromNode ? Number(fromNode) : undefined,
        toNode: toNode ? Number(toNode) : undefined,
        packetType: packetType || undefined,
      });
      setPackets(results);
    } catch (err) {
      setError((err as Error).message);
    }
  }

  async function onSelectPacket(packetId: number) {
    try {
      setError(null);
      const details = await getPacketPath(packetId);
      setPathData(details);
    } catch (err) {
      setError((err as Error).message);
    }
  }

  return (
    <main className="page">
      <header className="hero">
        <h1>Network Testing Dashboard</h1>
        <p>Raw MQTT envelopes, parsed Meshtastic packets, observation history, duplicates, and path tracing.</p>
      </header>

      {error ? <div className="error">{error}</div> : null}

      <section className="metrics-grid">
        <article className="card">
          <h2>Total MQTT</h2>
          <div className="value">{metrics?.total_messages ?? "-"}</div>
        </article>
        <article className="card">
          <h2>Parsed Inner Packets</h2>
          <div className="value">{metrics?.parsed_messages ?? "-"}</div>
        </article>
        <article className="card">
          <h2>Encoded Topic Unparsed</h2>
          <div className="value">{metrics?.encoded_unparsed_messages ?? "-"}</div>
        </article>
        <article className="card">
          <h2>Duplicates</h2>
          <div className="value">{metrics?.duplicate_logical_packets ?? "-"}</div>
        </article>
      </section>

      <section className="panel">
        <h2>Packet Search</h2>
        <form className="search-form" onSubmit={onSearch}>
          <input placeholder="from node" value={fromNode} onChange={(e) => setFromNode(e.target.value)} />
          <input placeholder="to node" value={toNode} onChange={(e) => setToNode(e.target.value)} />
          <input placeholder="packet type" value={packetType} onChange={(e) => setPacketType(e.target.value)} />
          <button type="submit">Search</button>
        </form>

        <div className="table-wrap">
          <table>
            <thead>
              <tr>
                <th>ID</th>
                <th>From</th>
                <th>To</th>
                <th>Type</th>
                <th>Obs</th>
                <th>Last Seen</th>
                <th>Action</th>
              </tr>
            </thead>
            <tbody>
              {packets.map((packet) => (
                <tr key={packet.id}>
                  <td>{packet.id}</td>
                  <td>{packet.from ?? "-"}</td>
                  <td>{packet.to ?? "-"}</td>
                  <td>{packet.type ?? "-"}</td>
                  <td>{packet.observation_count}</td>
                  <td>{formatDate(packet.last_seen_at)}</td>
                  <td>
                    <button onClick={() => void onSelectPacket(packet.id)}>Path</button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      <section className="panel two-col">
        <article>
          <h2>Node Stats</h2>
          <ul className="list">
            {nodes.map((node) => (
              <li key={`${node.node_num}-${node.packet_count}`}>
                <strong>{node.node_num ?? "unknown"}</strong>
                <span>{node.packet_count} packets</span>
                <span>{formatDate(node.last_seen_at)}</span>
              </li>
            ))}
          </ul>
        </article>

        <article>
          <h2>Duplicate Packets</h2>
          <ul className="list">
            {duplicates.map((packet) => (
              <li key={packet.id}>
                <strong>#{packet.id}</strong>
                <span>{packet.type ?? "unknown"}</span>
                <span>{packet.observation_count} observations</span>
              </li>
            ))}
          </ul>
        </article>
      </section>

      <section className="panel">
        <h2>Recent MQTT Messages</h2>
        <div className="table-wrap">
          <table>
            <thead>
              <tr>
                <th>ID</th>
                <th>Created</th>
                <th>Topic</th>
                <th>Status</th>
                <th>Payload</th>
              </tr>
            </thead>
            <tbody>
              {messages.map((message) => (
                <tr key={message.id}>
                  <td>{message.id}</td>
                  <td>{formatDate(message.created_at)}</td>
                  <td>{message.topic}</td>
                  <td>{message.parse_status}</td>
                  <td className="payload">{message.raw_payload.slice(0, 140)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      <section className="panel">
        <h2>Traceroute / Path</h2>
        {!pathData?.packet ? <p>Select a packet from search results.</p> : null}
        {pathData?.packet ? (
          <div className="path-grid">
            <div>
              <h3>Packet</h3>
              <p>ID: {pathData.packet.id}</p>
              <p>
                {pathData.packet.from ?? "-"} to {pathData.packet.to ?? "-"}
              </p>
              <p>Type: {pathData.packet.type ?? "-"}</p>
              <p>Observations: {pathData.packet.observation_count}</p>
            </div>
            <div>
              <h3>Route Hops</h3>
              <ul className="list">
                {pathData.route_hops.map((hop) => (
                  <li key={`${hop.hop_index}-${hop.from_node}-${hop.to_node}`}>
                    <strong>Hop {hop.hop_index}</strong>
                    <span>
                      {hop.from_node ?? "?"} to {hop.to_node ?? "?"}
                    </span>
                    <span>{formatDate(hop.observed_at)}</span>
                  </li>
                ))}
              </ul>
            </div>
          </div>
        ) : null}
      </section>
    </main>
  );
}
