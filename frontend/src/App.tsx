import { NavLink, Navigate, Route, Routes } from "react-router-dom";

import MessagesPage from "./pages/MessagesPage";
import NodesPage from "./pages/NodesPage";
import SendMessagePage from "./pages/SendMessagePage";
import SequenceReportsPage from "./pages/SequenceReportsPage";


export default function App() {
  return (
    <div className="app-shell">
      <header className="top-nav-wrap">
        <nav className="top-nav" aria-label="Primary navigation">
          <NavLink to="/" className={({ isActive }) => `nav-link${isActive ? " is-active" : ""}`}>
            Nodes
          </NavLink>
          <NavLink to="/messages/query" className={({ isActive }) => `nav-link${isActive ? " is-active" : ""}`}>
            Message Query
          </NavLink>
          <NavLink to="/messages/sequence" className={({ isActive }) => `nav-link${isActive ? " is-active" : ""}`}>
            Sequence Reports
          </NavLink>
          <NavLink to="/messages/send" className={({ isActive }) => `nav-link${isActive ? " is-active" : ""}`}>
            Send Message
          </NavLink>
        </nav>
      </header>

      <Routes>
        <Route path="/" element={<NodesPage />} />
        <Route path="/messages/query" element={<MessagesPage />} />
        <Route path="/messages/:nodeId" element={<MessagesPage />} />
        <Route path="/messages/sequence" element={<SequenceReportsPage />} />
        <Route path="/messages/:source/sequence/:sequenceNumber" element={<SequenceReportsPage />} />
        <Route path="/messages/send" element={<SendMessagePage />} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </div>
  );
}
