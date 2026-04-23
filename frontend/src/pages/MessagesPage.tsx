import { useEffect, useState } from "react";
import { useNavigate, useParams, useSearchParams } from "react-router-dom";

import { fetchQueryMessages, fetchSequenceReports } from "../api";
import type { MessageQueryResponse, SenderMessage, SequenceReportsResponse } from "../types";

export default function MessagesPage() {
  const { nodeId = "" } = useParams();
  const navigate = useNavigate();
  const [searchParams, setSearchParams] = useSearchParams();
  const [source, setSource] = useState("");
  const [destination, setDestination] = useState("");
  const [messageType, setMessageType] = useState("");
  const [messagesData, setMessagesData] = useState<MessageQueryResponse | null>(null);
  const [messagesLoading, setMessagesLoading] = useState(false);
  const [messagesError, setMessagesError] = useState<string | null>(null);
  const [selectedMessage, setSelectedMessage] = useState<SenderMessage | null>(null);
  const [reportsData, setReportsData] = useState<SequenceReportsResponse | null>(null);
  const [reportsLoading, setReportsLoading] = useState(false);
  const [reportsError, setReportsError] = useState<string | null>(null);

  useEffect(() => {
    const sourceFromQuery = searchParams.get("source") ?? "";
    const destinationFromQuery = searchParams.get("destination") ?? "";
    const messageTypeFromQuery = searchParams.get("messageType") ?? "";

    const initialSource = sourceFromQuery || nodeId;

    setSource(initialSource);
    setDestination(destinationFromQuery);
    setMessageType(messageTypeFromQuery);
  }, [nodeId, searchParams]);

  useEffect(() => {
    const load = async () => {
      setMessagesError(null);
      setMessagesLoading(true);
      setSelectedMessage(null);
      setReportsData(null);
      setReportsError(null);
      try {
        const data = await fetchQueryMessages({
          source: searchParams.get("source") ?? nodeId,
          destination: searchParams.get("destination") ?? "",
          messageType: searchParams.get("messageType") ?? "",
        });
        setMessagesData(data);
      } catch (err) {
        const message = err instanceof Error ? err.message : "Failed to query messages";
        setMessagesError(message);
        setMessagesData(null);
      } finally {
        setMessagesLoading(false);
      }
    };

    void load();
  }, [nodeId, searchParams]);

  const runQuery = () => {
    const next = new URLSearchParams();
    if (source.trim()) {
      next.set("source", source.trim());
    }
    if (destination.trim()) {
      next.set("destination", destination.trim());
    }
    if (messageType.trim()) {
      next.set("messageType", messageType.trim());
    }
    setSearchParams(next);
  };

  const clearQuery = () => {
    setSource("");
    setDestination("");
    setMessageType("");
    setSearchParams(new URLSearchParams());
  };

  const loadSequenceReports = async (message: SenderMessage) => {
    setSelectedMessage(message);
    setReportsLoading(true);
    setReportsError(null);
    try {
      const data = await fetchSequenceReports(message.source, message.sequence_number);
      setReportsData(data);
    } catch (err) {
      const message = err instanceof Error ? err.message : "Failed to fetch sequence reports";
      setReportsError(message);
      setReportsData(null);
    } finally {
      setReportsLoading(false);
    }
  };

  return (
    <main className="page">
      <section className="panel sender-panel">
        <p className="eyebrow">Network Testing Dashboard</p>
        <div className="panel-head">
          <h1>Message Query</h1>
          <button type="button" onClick={() => navigate("/")}>Back to Nodes</button>
        </div>

        <section className="sender-panel">
          <div className="filters-grid">
            <label>
              Source
              <input
                type="text"
                value={source}
                onChange={(event) => setSource(event.target.value)}
                placeholder="e.g. !aabbccdd"
              />
            </label>
            <label>
              Destination
              <input
                type="text"
                value={destination}
                onChange={(event) => setDestination(event.target.value)}
                placeholder="e.g. ^all"
              />
            </label>
            <label>
              Message Type
              <input
                type="text"
                value={messageType}
                onChange={(event) => setMessageType(event.target.value)}
                placeholder="e.g. route_discovery"
              />
            </label>
          </div>
          <div className="filter-actions">
            <button type="button" onClick={runQuery}>Run Query</button>
            <button type="button" onClick={clearQuery}>Clear</button>
          </div>
        </section>

        {messagesLoading ? <p className="muted">Loading messages...</p> : null}
        {messagesError ? <p className="error">{messagesError}</p> : null}

        {messagesData && !messagesLoading ? (
          <>
            <p className="muted">Found {messagesData.count} sequence entries.</p>
            <p className="muted">Only one row is shown per source and sequence number (reporter duplicates removed).</p>
            <div className="table-wrap">
              <table>
                <thead>
                  <tr>
                    <th>Source</th>
                    <th>Sequence Number</th>
                    <th>Destination</th>
                    <th>Portnum</th>
                    <th>Message Type</th>
                  </tr>
                </thead>
                <tbody>
                  {messagesData.messages.length === 0 ? (
                    <tr>
                      <td colSpan={5} className="empty">No messages found for the selected filters.</td>
                    </tr>
                  ) : (
                    messagesData.messages.map((message) => (
                      <tr key={`${message.source}-${message.sequence_number}`}>
                        <td>{message.source}</td>
                        <td>
                          <button
                            type="button"
                            className="link-button"
                            onClick={() => void loadSequenceReports(message)}
                          >
                            {message.sequence_number}
                          </button>
                        </td>
                        <td>{message.destination}</td>
                        <td>{message.portnum ?? "-"}</td>
                        <td>{message.message_type ?? "-"}</td>
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
            </div>
          </>
        ) : null}

        <section className="sender-panel reports-panel">
          <h2>Sequence Reports</h2>
          {selectedMessage === null ? <p className="muted">Click a sequence number to view all reports.</p> : null}
          {selectedMessage !== null ? <p className="muted">Selected: {selectedMessage.source} / {selectedMessage.sequence_number}</p> : null}
          {reportsLoading ? <p className="muted">Loading reports...</p> : null}
          {reportsError ? <p className="error">{reportsError}</p> : null}

          {reportsData && !reportsLoading ? (
            <>
              <p className="muted">Found {reportsData.count} reports for this sequence.</p>
              <div className="table-wrap">
                <table>
                  <thead>
                    <tr>
                      <th>Reporter</th>
                      <th>Destination</th>
                      <th>Portnum</th>
                      <th>Message Type</th>
                      <th>Next Hop</th>
                      <th>Relay Node</th>
                      <th>Request ID</th>
                      <th>Timestamp</th>
                    </tr>
                  </thead>
                  <tbody>
                    {reportsData.reports.length === 0 ? (
                      <tr>
                        <td colSpan={8} className="empty">No reports found for this sequence.</td>
                      </tr>
                    ) : (
                      reportsData.reports.map((report) => (
                        <tr key={report.id}>
                          <td>{report.reporter}</td>
                          <td>{report.destination}</td>
                          <td>{report.portnum ?? "-"}</td>
                          <td>{report.message_type ?? "-"}</td>
                          <td>{report.next_hop ?? "-"}</td>
                          <td>{report.relay_node ?? "-"}</td>
                          <td>{report.request_id ?? "-"}</td>
                          <td>{report.timestamp}</td>
                        </tr>
                      ))
                    )}
                  </tbody>
                </table>
              </div>
            </>
          ) : null}
        </section>
      </section>
    </main>
  );
}
