import { Navigate, Route, Routes } from "react-router-dom";
import AppShell from "./components/layout/AppShell";
import Dashboard from "./pages/Dashboard";
import Batches from "./pages/Batches";
import UploadBatch from "./pages/UploadBatch";
import Exceptions from "./pages/Exceptions";
import NotFound from "./pages/NotFound";

export default function App() {
  return (
    <AppShell>
      <Routes>
        <Route path="/" element={<Dashboard />} />
        <Route path="/batches" element={<Batches />} />
        <Route path="/upload" element={<UploadBatch />} />
        <Route path="/exceptions" element={<Exceptions />} />
        <Route path="/runs" element={<Navigate to="/batches" replace />} />
        <Route path="*" element={<NotFound />} />
      </Routes>
    </AppShell>
  );
}
