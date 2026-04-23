export type DummyViewModel = {
  message: string;
};

export type NodeRecord = {
  node_id: string;
  backend_id: string;
  last_byte: string;
};

export type SenderSequenceResponse = {
  node_id: string;
  count: number;
  sequence_numbers: number[];
};

export type SenderMessage = {
  sequence_number: number;
  source: string;
  destination: string;
  portnum: string | null;
  message_type: string | null;
};

export type SenderMessagesResponse = {
  node_id: string;
  count: number;
  messages: SenderMessage[];
};

export type MessageQueryFilters = {
  source: string;
  destination: string;
  message_type: string;
  portnum: string;
};

export type MessageQueryResponse = {
  count: number;
  filters: MessageQueryFilters;
  messages: SenderMessage[];
};

export type SenderMessageReport = {
  id: number;
  source: string;
  destination: string;
  reporter: string;
  sequence_number: number;
  timestamp: string;
  next_hop: string | null;
  relay_node: string | null;
  portnum: string | null;
  message_type: string | null;
  request_id: number | null;
};

export type SequenceReportsResponse = {
  node_id: string;
  sequence_number: number;
  count: number;
  reports: SenderMessageReport[];
};

export type Metrics = {
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

export type SendMessageResponse = {
  message?: string;
  sequence_number?: number;
  error?: string;
};

export type ClearMessagesResponse = {
  message: string;
  deleted_count: number;
};
