import type {
	MessageQueryResponse,
	NodeRecord,
	SendMessageResponse,
	SenderMessagesResponse,
	SenderSequenceResponse,
	SequenceReportsResponse,
} from "./types";


export async function fetchNodes(): Promise<NodeRecord[]> {
	const response = await fetch("/api/analyze/nodes");
	if (!response.ok) {
		throw new Error(`Nodes request failed: ${response.status}`);
	}
	return (await response.json()) as NodeRecord[];
}


export async function fetchSenderSequences(nodeId: string): Promise<SenderSequenceResponse> {
	const response = await fetch(`/api/analyze/nodes/${encodeURIComponent(nodeId)}/sender-sequences`);
	if (!response.ok) {
		throw new Error(`Sender sequences request failed: ${response.status}`);
	}
	return (await response.json()) as SenderSequenceResponse;
}


export async function fetchSenderMessages(nodeId: string): Promise<SenderMessagesResponse> {
	const response = await fetch(`/api/analyze/nodes/${encodeURIComponent(nodeId)}/messages`);
	if (!response.ok) {
		throw new Error(`Sender messages request failed: ${response.status}`);
	}
	return (await response.json()) as SenderMessagesResponse;
}


export async function fetchQueryMessages(filters: {
	source?: string;
	destination?: string;
	messageType?: string;
	portnum?: string;
}): Promise<MessageQueryResponse> {
	const params = new URLSearchParams();
	if (filters.source?.trim()) {
		params.set("source", filters.source.trim());
	}
	if (filters.destination?.trim()) {
		params.set("destination", filters.destination.trim());
	}
	if (filters.messageType?.trim()) {
		params.set("message_type", filters.messageType.trim());
	}
	if (filters.portnum?.trim()) {
		params.set("portnum", filters.portnum.trim());
	}

	const query = params.toString();
	const url = query ? `/api/analyze/messages/query?${query}` : "/api/analyze/messages/query";
	const response = await fetch(url);
	if (!response.ok) {
		throw new Error(`Message query request failed: ${response.status}`);
	}
	return (await response.json()) as MessageQueryResponse;
}


export async function fetchSequenceReports(nodeId: string, sequenceNumber: number): Promise<SequenceReportsResponse> {
	const response = await fetch(`/api/analyze/nodes/${encodeURIComponent(nodeId)}/messages/${sequenceNumber}/reports`);
	if (!response.ok) {
		throw new Error(`Sequence reports request failed: ${response.status}`);
	}
	return (await response.json()) as SequenceReportsResponse;
}


export async function sendMessage(params: {
	source: string;
	destination: string;
	payload: string;
}): Promise<SendMessageResponse> {
	const query = new URLSearchParams({
		source: params.source.trim(),
		destination: params.destination.trim(),
		payload: params.payload,
	});

	const response = await fetch(`/api/send?${query.toString()}`, {
		method: "POST",
	});

	const data = (await response.json()) as SendMessageResponse;
	if (!response.ok) {
		throw new Error(data.error ?? `Send request failed: ${response.status}`);
	}

	if (data.error) {
		throw new Error(data.error);
	}

	return data;
}