import { FormEvent, useState } from "react";

import { sendMessage } from "../api";

export default function SendMessagePage() {
  const [source, setSource] = useState("");
  const [destination, setDestination] = useState("");
  const [payload, setPayload] = useState("");
  const [isSending, setIsSending] = useState(false);
  const [resultMessage, setResultMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const onSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();

    if (!source.trim() || !destination.trim() || !payload.trim()) {
      setError("Source, destination, and payload are required.");
      setResultMessage(null);
      return;
    }

    setIsSending(true);
    setError(null);
    setResultMessage(null);

    try {
      const response = await sendMessage({
        source,
        destination,
        payload,
      });

      const sequenceText =
        typeof response.sequence_number === "number"
          ? ` Sequence number: ${response.sequence_number}.`
          : "";
      setResultMessage(`${response.message ?? "Message sent successfully."}${sequenceText}`);
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
        {resultMessage ? <p className="muted">{resultMessage}</p> : null}
      </section>
    </main>
  );
}
