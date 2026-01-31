import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { useNavigate } from "react-router-dom";
import { fetchFootprintsList } from "../../api/client";
import { 
  ArrowRight, ArrowLeft, Activity, Globe, User, ShieldAlert, 
  Database, AlertTriangle 
} from "lucide-react";
import { format } from "date-fns";

export default function Footprints() {
  const navigate = useNavigate();
  const [page, setPage] = useState(1);

  // Fetch data with caching
  const { data, isLoading } = useQuery({
    queryKey: ["footprints", page],
    queryFn: () => fetchFootprintsList(page),
    placeholderData: (previousData) => previousData, 
  });

  const logs = data?.results || [];
  const hasNext = !!data?.next;
  const hasPrev = !!data?.previous;

  if (isLoading) return <div className="p-8 text-gray-500">Loading logs...</div>;

  return (
    <div className="space-y-6">
      {/* HEADER */}
      <div className="flex justify-between items-end">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Footprints</h1>
          <p className="text-gray-500 text-sm">Raw request/response history across the system.</p>
        </div>
        
        {/* Pagination Controls */}
        <div className="flex items-center gap-2">
            <span className="text-xs text-gray-500 font-medium mr-2">
                Page {page} {data?.count ? `of ${Math.ceil(data.count / 50)}` : ''}
            </span>
            <div className="flex bg-white border border-gray-200 rounded-lg overflow-hidden shadow-sm">
                 <button
                    onClick={() => setPage((p) => Math.max(1, p - 1))}
                    disabled={!hasPrev}
                    className="px-3 py-2 text-xs font-medium text-gray-600 hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed border-r border-gray-200"
                  >
                    <ArrowLeft size={14} />
                  </button>
                  <button
                    onClick={() => setPage((p) => p + 1)}
                    disabled={!hasNext}
                    className="px-3 py-2 text-xs font-medium text-gray-600 hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    <ArrowRight size={14} />
                  </button>
            </div>
        </div>
      </div>

      {/* TABLE CONTAINER */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden">
        <table className="w-full text-left border-collapse">
          <thead>
            <tr className="bg-gray-50 border-b border-gray-200 text-xs uppercase text-gray-500 font-semibold">
              <th className="px-6 py-4 w-20">Method</th>
              <th className="px-6 py-4">Path</th>
              <th className="px-6 py-4">Status</th>
              <th className="px-6 py-4">Duration</th>
              <th className="px-6 py-4">DB</th>
              <th className="px-6 py-4">User ID</th>
              <th className="px-6 py-4 text-right">Date Created</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-100">
            {logs.map((log: any) => (
              <FootprintRow 
                key={log.id} 
                log={log} 
                onClick={() => navigate(`/footprints/${log.id}`)} 
              />
            ))}
            {logs.length === 0 && (
                <tr>
                    <td colSpan={7} className="px-6 py-8 text-center text-gray-400 text-sm">
                        No logs found.
                    </td>
                </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}

// --- ROW COMPONENT ---
function FootprintRow({ log, onClick }: { log: any; onClick: () => void }) {
  
  // Method Color Logic
  const methodColors: Record<string, string> = {
    get: "bg-blue-50 text-blue-700 border-blue-200",
    post: "bg-emerald-50 text-emerald-700 border-emerald-200",
    put: "bg-amber-50 text-amber-700 border-amber-200",
    patch: "bg-amber-50 text-amber-700 border-amber-200",
    delete: "bg-red-50 text-red-700 border-red-200",
  };
  const methodClass = methodColors[log.request_method.toLowerCase()] || "bg-gray-50 text-gray-700 border-gray-200";

  // Status Color Logic
  const isError = log.status_code >= 400;
  const statusColor = isError ? "text-red-600 bg-red-50 border-red-100" : "text-green-600 bg-green-50 border-green-100";

  return (
    <tr 
      onClick={onClick}
      className="transition-colors hover:bg-slate-50/50 cursor-pointer group"
    >
      <td className="px-6 py-4">
        <span className={`px-2 py-1 rounded text-[10px] font-bold uppercase tracking-wider border ${methodClass}`}>
          {log.request_method}
        </span>
      </td>
      
      <td className="px-6 py-4">
         <div className="flex items-center gap-2 group-hover:translate-x-1 transition-transform">
             <Globe size={14} className="text-gray-400" />
             <span className="font-mono text-sm text-gray-700 truncate max-w-xs block" title={log.request_path}>
                {log.request_path}
             </span>
         </div>
      </td>

      <td className="px-6 py-4">
         <span className={`px-2 py-1 rounded text-[10px] font-bold uppercase tracking-wider border flex items-center w-fit gap-1 ${statusColor}`}>
            {isError ? <ShieldAlert size={12}/> : <Activity size={12}/>}
            {log.status_code}
         </span>
      </td>

      {/* RESPONSE TIME & SLOW INDICATOR */}
      <td className="px-6 py-4">
        <div className="flex items-center gap-2">
            <span className="text-sm font-mono text-gray-700">
                {Math.round(log.response_time)}ms
            </span>
            {log.is_slow && (
                <span className="flex items-center gap-1 text-[10px] bg-amber-100 text-amber-700 px-1.5 py-0.5 rounded border border-amber-200 font-medium" title="Exceeds SLOW_REQUEST_THRESHOLD">
                    <AlertTriangle size={10} /> Slow
                </span>
            )}
        </div>
      </td>

      {/* DB QUERY COUNT */}
      <td className="px-6 py-4">
         <div className="flex items-center gap-1.5 text-sm text-gray-600">
            <Database size={14} className="text-gray-400" />
            <span className={`font-mono ${log.db_query_count > 50 ? 'text-red-600 font-bold' : ''}`}>
                {log.db_query_count}
            </span>
         </div>
      </td>

      {/* USER ID (FULL ANONYMOUS) */}
      <td className="px-6 py-4">
         <div className="flex items-center gap-2 text-sm text-gray-600">
            <User size={14} className="text-gray-400" />
            <span className="truncate max-w-[150px]">
                {log.request_user === "anonymous" ? "Anonymous" : log.request_user}
            </span>
         </div>
      </td>

      {/* CUSTOM DATE FORMAT */}
      <td className="px-6 py-4 text-right">
         <div className="flex items-center justify-end gap-2 text-xs font-mono text-gray-500">
            {format(new Date(log.created_at), "yyyy-MM-dd • HH-mm-ss")}
         </div>
      </td>
    </tr>
  );
}


