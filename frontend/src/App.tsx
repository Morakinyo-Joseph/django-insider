import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { HashRouter, Routes, Route, Navigate } from "react-router-dom";
import { DashboardLayout } from "./layout/DashboardLayout";

// Import Pages
import Dashboard from "./pages/Dashboard";
import Incidence from "./pages/Incidence";
import InvestigationRoom from "./pages/InvestigationRoom";
import ForensicsLab from "./pages/ForensicsLab";

// Create the Query Client (Cache Manager)
const queryClient = new QueryClient();

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      {/* We use HashRouter because Django serves the app from a sub-path */}
      <HashRouter> 
        <Routes>
          <Route element={<DashboardLayout />}>
            <Route path="/" element={<Dashboard />} />
            <Route path="/incidences" element={<Incidence />} />
            <Route path="/incidences/:incidenceId" element={<InvestigationRoom />} />
            <Route path="/footprints/:footprintId" element={<ForensicsLab />} />
            
            {/* Fallback */}
            <Route path="*" element={<Navigate to="/" replace />} />
          </Route>
        </Routes>
      </HashRouter>
    </QueryClientProvider>
  );
}

export default App;