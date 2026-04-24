import { FormEvent, useState } from "react";
import { useNavigate } from "react-router-dom";

import { sendMessage } from "../api";

type SentMessageResult = {
  source: string;
  message: string;
  sequenceNumber: number | null;
};

export default function SendMessagePage() {
  const navigate = useNavigate();
  const [source, setSource] = useState("");
  const [destination, setDestination] = useState("");
  const [payload, setPayload] = useState("");
  const [isSending, setIsSending] = useState(false);
  const [sentMessageResult, setSentMessageResult] = useState<SentMessageResult | null>(null);
  const [error, setError] = useState<string | null>(null);

  const onSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();

    if (!source.trim() || !destination.trim() || !payload.trim()) {
      setError("Source, destination, and payload are required.");
      setSentMessageResult(null);
      return;
    }

    setIsSending(true);
    setError(null);
    setSentMessageResult(null);

    try {
      const trimmedSource = source.trim();
      const response = await sendMessage({
        source: trimmedSource,
        destination,
        payload,
      });

      setSentMessageResult({
        source: trimmedSource,
        message: response.message ?? "Message sent successfully.",
        sequenceNumber: typeof response.sequence_number === "number" ? response.sequence_number : null,
      });
    } catch (err) {
      const message = err instanceof Error ? err.message : "Failed to send message";
      setError(message);
    } finally {
      setIsSending(false);
    }
  };

  return (
    <main className="page">
      <section className="panel sender-panel">
        <p className="eyebrow">Network Testing Dashboard</p>
        <div className="panel-head">
          <h1>Send Message</h1>
        </div>

        <form onSubmit={onSubmit} className="sender-panel">
          <div className="filters-grid send-grid">
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
            <label className="send-grid-full">
              Payload
              <textarea
                value={payload}
                onChange={(event) => setPayload(event.target.value)}
                placeholder="Message content"
                rows={5}
              />
            </label>
          </div>
          <div className="filter-actions">
            <button type="submit" disabled={isSending}>
              {isSending ? "Sending..." : "Send Message"}
            </button>
          </div>
        </form>

        {error ? <p className="error">{error}</p> : null}
        {sentMessageResult ? (
          <p className="muted">
            {sentMessageResult.message}
            {sentMessageResult.sequenceNumber !== null ? " Sequence number: " : ""}
            {sentMessageResult.sequenceNumber !== null ? (
              <button
                type="button"
                className="link-button"
                onClick={() =>
                  navigate(
                    `/messages/${encodeURIComponent(sentMessageResult.source)}/sequence/${sentMessageResult.sequenceNumber}`,
                  )
                }
              >
                {sentMessageResult.sequenceNumber}
              </button>
            ) : null}
            {sentMessageResult.sequenceNumber !== null ? "." : ""}
          </p>
        ) : null}
      </section>
    </main>
  );
}
