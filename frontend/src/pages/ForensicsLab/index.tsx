import { useParams, Link } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { fetchFootprint, fetchFootprintBreadcrumbs } from "../../api/client";
import { ChevronLeft, Database, Clock, Server, ArrowDownLeft, ArrowUpRight, Activity, Terminal, Copy } from "lucide-react"; // ADDED: Copy Icon
import { formatDistanceToNow } from "date-fns";

export default function ForensicsLab() {
  const { footprintId } = useParams();

  const { data: footprint, isLoading } = useQuery({
    queryKey: ["footprint", footprintId],
    queryFn: () => fetchFootprint(footprintId!),
  });

  const { data: breadcrumbs } = useQuery({
    queryKey: ["footprint", footprintId, "breadcrumbs"],
    queryFn: () => fetchFootprintBreadcrumbs(footprintId!),
    enabled: !!footprint, // Only fetch if footprint exists
  });

  if (isLoading) return <div className="p-8">Loading request data...</div>;
  if (!footprint) return <div className="p-8 text-red-600">Request trace not found.</div>;

  const isError = footprint.status_code >= 400;

  // ADDED: Replay Station Logic
  const handleCopyCurl = () => {
    let cmd = `curl -X ${footprint.request_method} "${footprint.request_path}"`;
    
    // Add Headers
    if (footprint.request_headers) {
      Object.entries(footprint.request_headers).forEach(([key, val]) => {
         // Cast val to string just in case
         cmd += ` \\\n  -H "${key}: ${String(val)}"`;
      });
    }

    // Add Body
    if (footprint.request_body && Object.keys(footprint.request_body).length > 0) {
      // Escape single quotes for shell
      const bodyStr = JSON.stringify(footprint.request_body).replace(/'/g, "'\\''");
      cmd += ` \\\n  -H "Content-Type: application/json"`;
      cmd += ` \\\n  -d '${bodyStr}'`;
    }

    navigator.clipboard.writeText(cmd);
    alert("cURL command copied to clipboard!");
  };

  return (
    <div className="space-y-6">
      <Link to={`/incidences/${footprint.incidence || ''}`} className="flex items-center gap-2 text-sm text-gray-500 hover:text-indigo-600 transition-colors">
        <ChevronLeft size={16} /> Back to Incidence
      </Link>

      {/* Header: The "Receipt" of the Request */}
      <div className="bg-white p-6 rounded-xl border border-gray-200 shadow-sm flex justify-between items-center">
        <div className="flex items-center gap-4">
          <div className={`w-12 h-12 rounded-full flex items-center justify-center font-bold text-lg ${
            isError ? 'bg-red-100 text-red-600' : 'bg-green-100 text-green-600'
          }`}>
            {footprint.status_code}
          </div>
          <div>
            <div className="flex items-center gap-2">
              <span className="font-mono font-bold text-gray-900 uppercase">{footprint.request_method}</span>
              <span className="font-mono text-gray-600">{footprint.request_path}</span>
            </div>
            <div className="text-xs text-gray-400 mt-1 font-mono">
              ID: {footprint.request_id} • User: {footprint.request_user}
            </div>
          </div>
        </div>
        <div className="text-right">
          <div className="text-2xl font-bold text-gray-900">{footprint.response_time.toFixed(1)}ms</div>
          <div className="text-xs text-gray-500 uppercase font-semibold tracking-wider">Latency</div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        
        {/* CENTER: Payload Inspector */}
        <div className="lg:col-span-2 space-y-6">
          
          {/* Request Body */}
          <div className="bg-white rounded-xl border border-gray-200 shadow-sm overflow-hidden">
            <div className="px-4 py-3 bg-gray-50 border-b border-gray-200 flex items-center justify-between">
              <div className="flex items-center gap-2">
                <ArrowUpRight size={16} className="text-blue-500" />
                <h3 className="text-xs font-bold text-gray-700 uppercase">Request Payload</h3>
              </div>
              {/* ADDED: Replay Button */}
              <button 
                onClick={handleCopyCurl}
                className="flex items-center gap-1 text-[10px] bg-white border border-gray-300 px-2 py-1 rounded hover:bg-gray-100 text-gray-700 font-medium"
              >
                <Copy size={12} /> Copy as cURL
              </button>
            </div>
            <div className="p-0">
              <JsonViewer data={footprint.request_body} />
            </div>
          </div>

          {/* Response Body */}
          <div className="bg-white rounded-xl border border-gray-200 shadow-sm overflow-hidden">
            <div className="px-4 py-3 bg-gray-50 border-b border-gray-200 flex items-center gap-2">
              <ArrowDownLeft size={16} className="text-green-500" />
              <h3 className="text-xs font-bold text-gray-700 uppercase">Response Body</h3>
            </div>
            <div className="p-0">
              <JsonViewer data={footprint.response_body} />
            </div>
          </div>

          {/* System Logs (Stdout/Stderr) */}
          <div className="bg-white rounded-xl border border-gray-200 shadow-sm overflow-hidden">
            <div className="px-4 py-3 bg-gray-50 border-b border-gray-200 flex items-center gap-2">
              <Terminal size={16} className="text-gray-500" />
              <h3 className="text-xs font-bold text-gray-700 uppercase">System Logs</h3>
            </div>
            <div className="p-0 bg-slate-900 min-h-[100px] max-h-[300px] overflow-y-auto">
              {!footprint.system_logs || footprint.system_logs.length === 0 ? (
                <div className="p-4 text-gray-500 text-xs font-mono italic">No system logs captured.</div>
              ) : (
                <div className="p-4 space-y-1">
                  {footprint.system_logs.map((log: string, i: number) => (
                    <div key={i} className="font-mono text-xs text-slate-300 border-b border-slate-800/50 pb-1 last:border-0">
                      {log}
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>

        </div>

        {/* SIDEBAR: Metrics & Breadcrumbs */}
        <div className="space-y-6">
          
          {/* System Metrics */}
          <div className="bg-white p-5 rounded-xl border border-gray-200 shadow-sm space-y-4">
            <h3 className="text-sm font-bold text-gray-900 uppercase tracking-tight">System Impact</h3>
            <div className="space-y-3">
              <div className="flex justify-between items-center text-sm">
                <div className="flex items-center gap-2 text-gray-500">
                  <Database size={14}/> <span>DB Queries</span>
                </div>
                {/* Visual indicator for N+1 */}
                <span className={`font-mono font-semibold ${
                   (footprint.db_query_count || 0) > 50 ? 'text-red-600' : 'text-gray-800'
                }`}>
                    {footprint.db_query_count}
                </span>
              </div>
              <div className="flex justify-between items-center text-sm">
                <div className="flex items-center gap-2 text-gray-500">
                  <Server size={14}/> <span>Server</span>
                </div>
                <span className="font-mono font-semibold text-gray-800">127.0.0.1</span>
              </div>
              <div className="flex justify-between items-center text-sm">
                <div className="flex items-center gap-2 text-gray-500">
                  <Clock size={14}/> <span>Timestamp</span>
                </div>
                <span className="font-mono text-xs text-gray-800">
                  {new Date(footprint.created_at).toLocaleTimeString()}
                </span>
              </div>
            </div>
          </div>

          {/* Breadcrumbs (Time Machine) */}
          <div className="bg-white rounded-xl border border-gray-200 shadow-sm overflow-hidden">
             <div className="p-4 border-b border-gray-100 bg-amber-50/50">
              <h3 className="text-xs font-bold text-amber-900 uppercase flex items-center gap-2">
                <Activity size={14} /> User Footprints (Last 5 min)
              </h3>
            </div>
            <div className="divide-y divide-gray-100">
              {breadcrumbs?.map((crumb) => (
                <div key={crumb.id} className={`p-3 text-xs flex justify-between items-center ${
                    crumb.id === footprint.id ? 'bg-indigo-50 border-l-2 border-indigo-500' : ''
                }`}>
                  <div className="flex items-center gap-2">
                     <span className={`font-bold ${crumb.status_code >= 400 ? 'text-red-500' : 'text-green-600'}`}>
                        {crumb.request_method}
                     </span>
                     <span className="text-gray-600 truncate max-w-[120px]">{crumb.request_path}</span>
                  </div>
                  <span className="text-gray-400 font-mono">
                    {formatDistanceToNow(new Date(crumb.created_at))} ago
                  </span>
                </div>
              ))}
              {(!breadcrumbs || breadcrumbs.length === 0) && (
                 <div className="p-4 text-gray-400 text-xs text-center">No prior actions found.</div>
              )}
            </div>
          </div>

        </div>
      </div>
    </div>
  );
}

// Simple Dark Mode JSON Viewer
function JsonViewer({ data }: { data: any }) {
  if (!data) return <div className="p-4 text-gray-400 text-sm italic">Empty</div>;
  
  return (
    <pre className="bg-slate-900 text-slate-300 p-4 text-xs font-mono overflow-x-auto">
      {JSON.stringify(data, null, 2)}
    </pre>
  );
}