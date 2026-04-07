import { DuplicatePacket, LogicalPacket, Metrics, NodeStat, PacketPath, RecentMessage } from "./types";

const API_BASE =
  (import.meta as ImportMeta & { env?: Record<string, string> }).env?.VITE_API_BASE_URL ??
  "http://localhost:8000/api";

async function fetchJson<T>(path: string): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`);
  if (!response.ok) {
    throw new Error(`Request failed (${response.status}) for ${path}`);
  }
  return response.json() as Promise<T>;
}

export function getMetrics() {
  return fetchJson<Metrics>("/metrics");
}

export function getNodeStats() {
  return fetchJson<NodeStat[]>("/nodes/stats?limit=25");
}

export function getRecentMessages() {
  return fetchJson<RecentMessage[]>("/messages/recent?limit=25");
}

export function searchPackets(params: {
  fromNode?: number;
  toNode?: number;
  packetType?: string;
  sessionId?: number;
}) {
  const query = new URLSearchParams();
  if (params.fromNode !== undefined) query.set("from_node", String(params.fromNode));
  if (params.toNode !== undefined) query.set("to_node", String(params.toNode));
  if (params.packetType) query.set("packet_type", params.packetType);
  if (params.sessionId !== undefined) query.set("session_id", String(params.sessionId));
  query.set("limit", "50");
  return fetchJson<LogicalPacket[]>(`/packets/search?${query.toString()}`);
}

export function getDuplicates() {
  return fetchJson<DuplicatePacket[]>("/packets/duplicates?limit=25");
}

export function getPacketPath(packetId: number) {
  return fetchJson<PacketPath>(`/packets/${packetId}/path`);
}
