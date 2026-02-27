import { useState, useMemo, useEffect } from "react";
import { useQuery } from "@tanstack/react-query";
import { useNavigate, useSearchParams } from "react-router-dom";
import { fetchFootprintsList } from "../../api/client";
import { 
  ArrowRight, ArrowLeft, Activity, Globe, User, ShieldAlert, 
  Database, AlertTriangle, Search, Filter, X, Check 
} from "lucide-react";
import { format } from "date-fns";
import { format, subMinutes, subHours, subDays, startOfDay } from "date-fns";
import { TableRowSkeleton } from "../../components/Skeleton";

export default function Footprints() {
  const navigate = useNavigate();
  
  // --- NEW SEARCH FIELD LOGIC START ---
  const [searchParams, setSearchParams] = useSearchParams();
  
  const activeFilters = useMemo(() => {
    const filters: Record<string, string> = {};
    searchParams.forEach((value, key) => {
      if (value && key !== "page") filters[key] = value;
    });
    return filters;
  }, [searchParams]);

  const [isFilterOpen, setIsFilterOpen] = useState(false);
  const [draftFilters, setDraftFilters] = useState<Record<string, string>>(activeFilters);
  
  const urlPage = parseInt(searchParams.get("page") || "1", 10);
  const [page, setLocalPage] = useState(urlPage);

  useEffect(() => {
    setDraftFilters(activeFilters);
    setLocalPage(urlPage);
  }, [activeFilters, urlPage]);

  // Overriding setPage to keep your original pagination untouched
  const setPage = (updater: any) => {
    const newPage = typeof updater === 'function' ? updater(page) : updater;
    const newParams = new URLSearchParams(searchParams);
    newParams.set("page", newPage.toString());
    setSearchParams(newParams);
  };

  const handleDraftChange = (key: string, value: string) => {
    setDraftFilters(prev => ({ ...prev, [key]: value }));
  };

  const applyFilters = () => {
    const newParams = new URLSearchParams();
    Object.entries(draftFilters).forEach(([key, value]) => {
      if (value) newParams.set(key, value);
    });
    newParams.set("page", "1");
    setSearchParams(newParams);
  };

  const clearFilters = () => {
    setDraftFilters({});
    setSearchParams(new URLSearchParams({ page: "1" }));
    setIsFilterOpen(false);
  };

  const applyPreset = (type: '15m' | '1h' | '24h' | 'today') => {
    const now = new Date();
    let start: Date;
    
    switch(type) {
        case '15m': start = subMinutes(now, 15); break;
        case '1h': start = subHours(now, 1); break;
        case '24h': start = subDays(now, 1); break;
        case 'today': start = startOfDay(now); break;
    }
    
    handleDraftChange("created_after", format(start, "yyyy-MM-dd'T'HH:mm"));
    handleDraftChange("created_before", ""); // Clear end date to mean "now"
  };

  const activeFilterCount = Object.keys(activeFilters).length;
  // --- NEW SEARCH FIELD LOGIC END ---

  // Fetch data with caching
  // Added isFetching to detect background updates
  const { data, isLoading, isFetching } = useQuery({
    queryKey: ["footprints", page, activeFilters],
    queryFn: () => fetchFootprintsList(page, activeFilters),
    placeholderData: (previousData) => previousData, 
  });

  const logs = data?.results || [];
  const hasNext = !!data?.next;
  const hasPrev = !!data?.previous;

  // Hybrid Loader Logic
  const showSkeleton = isLoading; 
  const isPaginationLoading = isFetching && !isLoading;

  return (
    <div className="space-y-6">
      {/* CSS Animation for the Progress Bar */}
      <style>{`
        @keyframes indeterminate-slide {
          0% { transform: translateX(-100%); }
          100% { transform: translateX(100%); }
        }
      `}</style>

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
                    onClick={() => setPage((p: number) => Math.max(1, p - 1))}
                    disabled={!hasPrev || isPaginationLoading}
                    className="px-3 py-2 text-xs font-medium text-gray-600 hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed border-r border-gray-200"
                  >
                    <ArrowLeft size={14} />
                  </button>
                  <button
                    onClick={() => setPage((p: number) => p + 1)}
                    disabled={!hasNext || isPaginationLoading}
                    className="px-3 py-2 text-xs font-medium text-gray-600 hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    <ArrowRight size={14} />
                  </button>
            </div>
        </div>
      </div>

      {/* --- NEW SEARCH UI BLOCK START --- */}
      <div className="flex items-center gap-3 w-full">
        <div className="relative flex-grow sm:w-64">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" size={16} />
          <input 
            type="text" 
            placeholder="Search payloads or IDs..."
            className="w-full pl-9 pr-3 py-2 text-sm border border-gray-200 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-purple-500 outline-none transition-all"
            value={draftFilters.global_search || ""}
            onChange={(e) => handleDraftChange("global_search", e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && applyFilters()}
          />
        </div>
        <button 
          onClick={() => setIsFilterOpen(!isFilterOpen)}
          className={`flex items-center gap-2 px-3 py-2 text-sm font-medium rounded-lg border transition-colors ${
            activeFilterCount > 0 || isFilterOpen 
              ? 'bg-purple-50 border-purple-200 text-purple-700' 
              : 'bg-white border-gray-200 text-gray-600 hover:bg-gray-50'
          }`}
        >
          <Filter size={16} />
          Filters {activeFilterCount > 0 && <span className="bg-purple-200 text-purple-800 text-[10px] px-1.5 py-0.5 rounded-full">{activeFilterCount}</span>}
        </button>
      </div>

      {isFilterOpen && (
        <div className="bg-gray-50 border border-gray-200 rounded-xl p-4 shadow-inner">
          <div className="flex justify-between items-center mb-4">
            <h3 className="text-sm font-semibold text-gray-700">Advanced Filters</h3>
            {activeFilterCount > 0 && (
              <button onClick={clearFilters} className="text-xs text-red-600 hover:text-red-800 font-medium flex items-center gap-1">
                <X size={12} /> Clear All
              </button>
            )}
          </div>
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-4">
            <div>
              <label className="block text-xs font-medium text-gray-500 mb-1">User ID / Email</label>
              <input 
                type="text" 
                placeholder="e.g. joseph@expedier.co"
                className="w-full p-2 text-sm border border-gray-200 rounded bg-white"
                value={draftFilters.request_user || ""}
                onChange={(e) => handleDraftChange("request_user", e.target.value)}
                onKeyDown={(e) => e.key === 'Enter' && applyFilters()}
              />
            </div>
            <div>
              <label className="block text-xs font-medium text-gray-500 mb-1">Endpoint Path</label>
              <input 
                type="text" 
                placeholder="e.g. /api/checkout"
                className="w-full p-2 text-sm border border-gray-200 rounded bg-white"
                value={draftFilters.request_path || ""}
                onChange={(e) => handleDraftChange("request_path", e.target.value)}
                onKeyDown={(e) => e.key === 'Enter' && applyFilters()}
              />
            </div>
            <div>
              <label className="block text-xs font-medium text-gray-500 mb-1">HTTP Method</label>
              <select 
                className="w-full p-2 text-sm border border-gray-200 rounded bg-white text-gray-700"
                value={draftFilters.request_method || ""}
                onChange={(e) => handleDraftChange("request_method", e.target.value)}
              >
                <option value="">All Methods</option>
                <option value="get">GET</option>
                <option value="post">POST</option>
                <option value="put">PUT</option>
                <option value="patch">PATCH</option>
                <option value="delete">DELETE</option>
              </select>
            </div>
            <div>
              <label className="block text-xs font-medium text-gray-500 mb-1">Status Code Types</label>
              <select 
                className="w-full p-2 text-sm border border-gray-200 rounded bg-white text-gray-700"
                value={
                  draftFilters.status_code__in?.includes("500") ? "5xx" :
                  draftFilters.status_code__in?.includes("400") ? "4xx" : 
                  ""
                }
                onChange={(e) => {
                  if (e.target.value === "5xx") handleDraftChange("status_code__in", "500,502,503,504");
                  else if (e.target.value === "4xx") handleDraftChange("status_code__in", "400,401,403,404,422");
                  else handleDraftChange("status_code__in", "");
                }}
              >
                <option value="">All Statuses</option>
                <option value="5xx">Server Errors (5xx)</option>
                <option value="4xx">Client Errors (4xx)</option>
              </select>
            </div>
            
            {/* Time Range Filter (Spans 2 Columns) */}
            <div className="md:col-span-2">
              <div className="flex justify-between items-end mb-1">
                <label className="block text-xs font-medium text-gray-500">Time Range</label>
                <div className="flex gap-1">
                  {['15m', '1h', '24h', 'Today'].map((label) => (
                    <button
                      key={label}
                      onClick={() => applyPreset(label.toLowerCase().replace(' ', '') as any)}
                      className="px-2 py-0.5 text-[10px] bg-purple-50 hover:bg-purple-100 text-purple-700 rounded border border-purple-100 transition-colors font-medium"
                    >
                      {label}
                    </button>
                  ))}
                </div>
              </div>
              <div className="flex items-center gap-2">
                <input 
                  type="datetime-local" 
                  className="w-full p-2 text-sm border border-gray-200 rounded bg-white text-gray-600"
                  value={draftFilters.created_after || ""}
                  onChange={(e) => handleDraftChange("created_after", e.target.value)}
                />
                <span className="text-gray-400 text-xs">to</span>
                <input 
                  type="datetime-local" 
                  className="w-full p-2 text-sm border border-gray-200 rounded bg-white text-gray-600"
                  value={draftFilters.created_before || ""}
                  onChange={(e) => handleDraftChange("created_before", e.target.value)}
                />
              </div>
            </div>

            <div>
              <label className="block text-xs font-medium text-gray-500 mb-1">Min. Response Time (ms)</label>
              <input 
                type="number" 
                placeholder="e.g. 2000"
                className="w-full p-2 text-sm border border-gray-200 rounded bg-white"
                value={draftFilters.min_response_time || ""}
                onChange={(e) => handleDraftChange("min_response_time", e.target.value)}
                onKeyDown={(e) => e.key === 'Enter' && applyFilters()}
              />
            </div>
             <div>
              <label className="block text-xs font-medium text-gray-500 mb-1">Min. DB Queries</label>
              <input 
                type="number" 
                placeholder="e.g. 50"
                className="w-full p-2 text-sm border border-gray-200 rounded bg-white"
                value={draftFilters.min_db_queries || ""}
                onChange={(e) => handleDraftChange("min_db_queries", e.target.value)}
                onKeyDown={(e) => e.key === 'Enter' && applyFilters()}
              />
            </div>
          </div>
          <div className="flex justify-end pt-2 border-t border-gray-200">
             <button 
                onClick={applyFilters}
                className="flex items-center gap-1 bg-purple-600 hover:bg-purple-700 text-white px-4 py-2 rounded-lg text-sm font-medium transition-colors"
             >
                <Check size={14} /> Apply Filters
             </button>
          </div>
        </div>
      )}
      {/* --- NEW SEARCH UI BLOCK END --- */}

      {/* TABLE CONTAINER */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden relative">
        
        {/* Purple Progress Bar (Visible only during pagination) */}
        {isPaginationLoading && (
           <div className="absolute top-0 left-0 w-full h-0.5 bg-purple-100 overflow-hidden z-10">
             {/* Applied the animation style manually here */}
             <div 
               className="w-full h-full bg-purple-600" 
               style={{ animation: 'indeterminate-slide 1s infinite linear' }}
             ></div>
           </div>
        )}

        {/* Opacity Dip Wrapper */}
        <div className={`transition-opacity duration-200 ${isPaginationLoading ? 'opacity-50 pointer-events-none' : ''}`}>
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
              {showSkeleton ? (
                // Skeleton Rows (Initial Load)
                Array.from({ length: 10 }).map((_, i) => (
                  <TableRowSkeleton key={i} cols={7} />
                ))
              ) : (
                // Real Data
                logs.map((log: any) => (
                  <FootprintRow 
                    key={log.id} 
                    log={log} 
                    onClick={() => navigate(`/footprints/${log.id}`)} 
                  />
                ))
              )}
              
              {!showSkeleton && logs.length === 0 && (
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