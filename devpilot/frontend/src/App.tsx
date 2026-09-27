import { HashRouter, Navigate, Route, Routes } from "react-router-dom";

import Landing from "./pages/Landing";
import RepoIntel from "./pages/RepoIntel";
import Workspace from "./pages/Workspace";

export default function App() {
  return (
    <HashRouter>
      <Routes>
        <Route path="/" element={<Landing />} />
        <Route path="/workspace/:projectId" element={<Workspace />} />
        <Route path="/repo-intel/:projectId" element={<RepoIntel />} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </HashRouter>
  );
}
