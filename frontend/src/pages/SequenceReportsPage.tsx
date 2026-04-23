import { FormEvent, useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";

import { fetchSequenceReports } from "../api";
import type { SequenceReportsResponse } from "../types";

export default function SequenceReportsPage() {
  const { source = "", sequenceNumber = "" } = useParams();
  const navigate = useNavigate();
  const [searchSource, setSearchSource] = useState("");
  const [searchSequenceNumber, setSearchSequenceNumber] = useState("");
  const [reportsData, setReportsData] = useState<SequenceReportsResponse | null>(null);
  const [reportsLoading, setReportsLoading] = useState(false);
  const [reportsError, setReportsError] = useState<string | null>(null);
  const [showForm, setShowForm] = useState(true);

  useEffect(() => {
    if (!source || !sequenceNumber) {
      setShowForm(true);
      return;
    }

    setShowForm(false);
    const load = async () => {
      setReportsError(null);
      setReportsLoading(true);
      setReportsData(null);
      try {
        const sequenceNum = parseInt(sequenceNumber, 10);
        if (isNaN(sequenceNum)) {
          throw new Error("Invalid sequence number");
        }
        const data = await fetchSequenceReports(source, sequenceNum);
        setReportsData(data);
      } catch (err) {
        const message = err instanceof Error ? err.message : "Failed to fetch sequence reports";
        setReportsError(message);
        setReportsData(null);
      } finally {
        setReportsLoading(false);
      }
    };

    void load();
  }, [source, sequenceNumber]);

  const handleSearchSubmit = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();

    if (!searchSource.trim() || !searchSequenceNumber.trim()) {
      setReportsError("Source and sequence number are required.");
      return;
    }

    navigate(`/messages/${encodeURIComponent(searchSource.trim())}/sequence/${encodeURIComponent(searchSequenceNumber.trim())}`);
  };

  const goToRequestSequenceReports = (requestId: number) => {
    navigate(`/messages/${encodeURIComponent(source)}/sequence/${requestId}`);
  };

  return (
    <main className="page">
      <section className="panel sender-panel">
        <p className="eyebrow">Network Testing Dashboard</p>
        <div className="panel-head">
          <h1>Sequence Reports</h1>
        </div>

        {showForm ? (
          <form onSubmit={handleSearchSubmit} className="sender-panel">
            <div className="filters-grid">
              <label>
                Source
                <input
                  type="text"
                  value={searchSource}
                  onChange={(event) => setSearchSource(event.target.value)}
                  placeholder="e.g. !aabbccdd"
                />
              </label>
              <label>
                Sequence Number
                <input
                  type="number"
                  value={searchSequenceNumber}
                  onChange={(event) => setSearchSequenceNumber(event.target.value)}
                  placeholder="e.g. 1"
                />
              </label>
            </div>
            <div className="filter-actions">
              <button type="submit">Search Reports</button>
            </div>
            {reportsError ? <p className="error">{reportsError}</p> : null}
          </form>
        ) : (
          <>
            <p className="muted">Source: {source}</p>
            <p className="muted">Sequence: {sequenceNumber}</p>

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
                        <th>Hops Away</th>
                        <th>Next Hop</th>
                        <th>Relay Node</th>
                        <th>Request ID</th>
                        <th>Timestamp</th>
                      </tr>
                    </thead>
                    <tbody>
                      {reportsData.reports.length === 0 ? (
                        <tr>
                          <td colSpan={9} className="empty">No reports found for this sequence.</td>
                        </tr>
                      ) : (
                        reportsData.reports.map((report) => (
                          <tr key={report.id}>
                            <td>{report.reporter}</td>
                            <td>{report.destination}</td>
                            <td>{report.portnum ?? "-"}</td>
                            <td>{report.message_type ?? "-"}</td>
                            <td>{report.hops_away ?? "-"}</td>
                            <td>{report.next_hop ?? "-"}</td>
                            <td>{report.relay_node ?? "-"}</td>
                            <td>
                              {report.request_id !== null ? (
                                <button
                                  type="button"
                                  className="link-button"
                                  onClick={() => goToRequestSequenceReports(report.request_id!)}
                                >
                                  {report.request_id}
                                </button>
                              ) : (
                                "-"
                              )}
                            </td>
                            <td>{report.timestamp}</td>
                          </tr>
                        ))
                      )}
                    </tbody>
                  </table>
                </div>
              </>
            ) : null}
          </>
        )}
      </section>
    </main>
  );
}
