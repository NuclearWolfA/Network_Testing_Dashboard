export type DummyViewModel = {
  message: string;
};export type Metrics = {
  total_messages: number;
  parsed_messages: number;
  encoded_unparsed_messages: number;
  parse_rate: number;
  logical_packets: number;
  packet_observations: number;
  duplicate_logical_packets: number;
};

export type NodeStat = {
  node_num: number | null;
  packet_count: number;
  last_seen_at: string | null;
  short_name: string | null;
  long_name: string | null;
};

export type RecentMessage = {
  id: number;
  topic: string;
  qos: number;
  retain: boolean;
  created_at: string;
  connection_id: string | null;
  parse_status: string;
  raw_payload: string;
};

export type LogicalPacket = {
  id: number;
  session_id: number | null;
  fingerprint: string;
  inner_packet_id: string | null;
  channel: string | null;
  from: number | null;
  hop_start: number | null;
  hops_away: number | null;
  sender: number | null;
  timestamp: string | null;
  to: number | null;
  type: string | null;
  payload: unknown;
  next_hop: number | null;
  relay_node: number | null;
  rssi: number | null;
  snr: number | null;
  first_seen_at: string;
  last_seen_at: string;
  observation_count: number;
};

export type DuplicatePacket = {
  id: number;
  fingerprint: string;
  inner_packet_id: string | null;
  from: number | null;
  to: number | null;
  type: string | null;
  timestamp: string | null;
  observation_count: number;
  last_seen_at: string;
};

export type PacketPath = {
  packet: {
    id: number;
    from: number | null;
    to: number | null;
    type: string | null;
    timestamp: string | null;
    observation_count: number;
  } | null;
  route_hops: Array<{
    hop_index: number;
    from_node: number | null;
    to_node: number | null;
    observed_at: string;
    meta: Record<string, unknown>;
  }>;
  observations: Array<{
    id: number;
    mqtt_message_id: number;
    observed_at: string;
    topic: string;
    connection_id: string | null;
    hop_start: number | null;
    hops_away: number | null;
    next_hop: number | null;
    relay_node: number | null;
    rssi: number | null;
    snr: number | null;
  }>;
};
