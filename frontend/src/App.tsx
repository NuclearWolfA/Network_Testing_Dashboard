import { Navigate, Route, Routes } from "react-router-dom";

import MessagesPage from "./pages/MessagesPage";
import NodesPage from "./pages/NodesPage";
import SequenceReportsPage from "./pages/SequenceReportsPage";


export default function App() {
  return (
    <Routes>
      <Route path="/" element={<NodesPage />} />
      <Route path="/messages/query" element={<MessagesPage />} />
      <Route path="/messages/:nodeId" element={<MessagesPage />} />
      <Route path="/messages/:source/sequence/:sequenceNumber" element={<SequenceReportsPage />} />
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}
