import { useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";

import { fetchSequenceReports } from "../api";
import type { SequenceReportsResponse } from "../types";

export default function SequenceReportsPage() {
  const { source = "", sequenceNumber = "" } = useParams();
  const navigate = useNavigate();
  const [reportsData, setReportsData] = useState<SequenceReportsResponse | null>(null);
  const [reportsLoading, setReportsLoading] = useState(false);
  const [reportsError, setReportsError] = useState<string | null>(null);

  useEffect(() => {
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

  const goToRequestSequenceReports = (requestId: number) => {
    navigate(`/messages/${encodeURIComponent(source)}/sequence/${requestId}`);
  };

  return (
    <main className="page">
      <section className="panel sender-panel">
        <p className="eyebrow">Network Testing Dashboard</p>
        <div className="panel-head">
          <h1>Sequence Reports</h1>
          <button type="button" onClick={() => navigate(-1)}>Back to Messages</button>
        </div>
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
      </section>
    </main>
  );
}
