import { useEffect, useState } from "react";
import { useNavigate, useParams, useSearchParams } from "react-router-dom";

import { clearMessagesTable, fetchQueryMessages } from "../api";
import type { MessageQueryResponse, SenderMessage } from "../types";

export default function MessagesPage() {
  const { nodeId = "" } = useParams();
  const navigate = useNavigate();
  const [searchParams, setSearchParams] = useSearchParams();
  const [source, setSource] = useState("");
  const [destination, setDestination] = useState("");
  const [messageType, setMessageType] = useState("");
  const [portnum, setPortnum] = useState("");
  const [messagesData, setMessagesData] = useState<MessageQueryResponse | null>(null);
  const [messagesLoading, setMessagesLoading] = useState(false);
  const [messagesError, setMessagesError] = useState<string | null>(null);
  const [isClearing, setIsClearing] = useState(false);
  const [clearStatus, setClearStatus] = useState<string | null>(null);

  useEffect(() => {
    const sourceFromQuery = searchParams.get("source") ?? "";
    const destinationFromQuery = searchParams.get("destination") ?? "";
    const messageTypeFromQuery = searchParams.get("messageType") ?? "";
    const portnumFromQuery = searchParams.get("portnum") ?? "";

    const initialSource = sourceFromQuery || nodeId;

    setSource(initialSource);
    setDestination(destinationFromQuery);
    setMessageType(messageTypeFromQuery);
    setPortnum(portnumFromQuery);
  }, [nodeId, searchParams]);

  useEffect(() => {
    const load = async () => {
      setMessagesError(null);
      setMessagesLoading(true);
      try {
        const data = await fetchQueryMessages({
          source: searchParams.get("source") ?? nodeId,
          destination: searchParams.get("destination") ?? "",
          messageType: searchParams.get("messageType") ?? "",
          portnum: searchParams.get("portnum") ?? "",
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
    if (portnum.trim()) {
      next.set("portnum", portnum.trim());
    }
    setSearchParams(next);
  };

  const clearQuery = () => {
    setSource("");
    setDestination("");
    setMessageType("");
    setPortnum("");
    setSearchParams(new URLSearchParams());
  };

  const clearMessages = async () => {
    const confirmed = window.confirm("This will delete all rows in the messages table. Continue?");
    if (!confirmed) {
      return;
    }

    setIsClearing(true);
    setMessagesError(null);
    setClearStatus(null);
    try {
      const response = await clearMessagesTable();
      setClearStatus(`${response.message}. Deleted rows: ${response.deleted_count}.`);
      const refreshed = await fetchQueryMessages({
        source: searchParams.get("source") ?? nodeId,
        destination: searchParams.get("destination") ?? "",
        messageType: searchParams.get("messageType") ?? "",
        portnum: searchParams.get("portnum") ?? "",
      });
      setMessagesData(refreshed);
    } catch (err) {
      const message = err instanceof Error ? err.message : "Failed to clear messages table";
      setMessagesError(message);
    } finally {
      setIsClearing(false);
    }
  };

  const goToSequenceReports = (message: SenderMessage) => {
    navigate(`/messages/${encodeURIComponent(message.source)}/sequence/${message.sequence_number}`);
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
            <label>
              Portnum
              <input
                type="text"
                value={portnum}
                onChange={(event) => setPortnum(event.target.value)}
                placeholder="e.g. NODEINFO_APP"
              />
            </label>
          </div>
          <div className="filter-actions">
            <button type="button" onClick={runQuery}>Run Query</button>
            <button type="button" onClick={clearQuery}>Clear</button>
            <button type="button" onClick={() => void clearMessages()} disabled={isClearing}>
              {isClearing ? "Clearing..." : "Clear Messages Table"}
            </button>
          </div>
        </section>

        {messagesLoading ? <p className="muted">Loading messages...</p> : null}
        {messagesError ? <p className="error">{messagesError}</p> : null}
        {clearStatus ? <p className="muted">{clearStatus}</p> : null}

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
                            onClick={() => goToSequenceReports(message)}
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
      </section>
    </main>
  );
}
