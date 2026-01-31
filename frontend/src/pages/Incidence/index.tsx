import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { fetchIncidences, bulkResolveIncidences, bulkIgnoreIncidences } from "../../api/client";
import { Search, ArrowUpDown, User, Check, XCircle } from "lucide-react";
import { Link } from "react-router-dom";
import { formatDistanceToNow } from "date-fns";
import { TableRowSkeleton } from "../../components/Skeleton";

export default function Incidence() {
  const queryClient = useQueryClient();
  
  // State for Filtering and Selection
  const [activeFilter, setActiveFilter] = useState<string>(""); // '' | 'new' | 'regressions'
  const [selectedIds, setSelectedIds] = useState<number[]>([]);

  // Fetch Data with Filter
  const { data: incidences, isLoading, isFetching } = useQuery({
    queryKey: ["incidences", activeFilter],
    queryFn: () => fetchIncidences(activeFilter),
  });

  // Hybrid Loader Logic
  const showSkeleton = isLoading;
  const isFilterLoading = isFetching && !isLoading;

  // Bulk Resolve Mutation
  const resolveMutation = useMutation({
    mutationFn: bulkResolveIncidences,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["incidences"] });
      setSelectedIds([]); // Clear selection
    },
  });

  // Bulk Ignore Mutation
  const ignoreMutation = useMutation({
    mutationFn: bulkIgnoreIncidences,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["incidences"] });
      setSelectedIds([]); // Clear selection
    },
  });

  // Handlers
  const handleSelectAll = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.checked && incidences) {
      setSelectedIds(incidences.map(i => i.id));
    } else {
      setSelectedIds([]);
    }
  };

  const handleSelectRow = (id: number) => {
    setSelectedIds(prev => 
      prev.includes(id) ? prev.filter(i => i !== id) : [...prev, id]
    );
  };

  return (
    <div className="space-y-6">
      <style>{`
        @keyframes indeterminate-slide {
          0% { transform: translateX(-100%); }
          100% { transform: translateX(100%); }
        }
      `}</style>

      <div className="flex justify-between items-end">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Incidence</h1>
          <p className="text-gray-500 text-sm">Triage and manage reported exceptions.</p>
        </div>
        
        {/* Simple Search/Filter Bar */}
        <div className="flex gap-2">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" size={16} />
            <input 
              type="text" 
              placeholder="Search incidences..." 
              className="pl-10 pr-4 py-2 border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
            />
          </div>
          
          {/* Filter Dropdown Logic */}
          <div className="flex bg-white border border-gray-200 rounded-lg overflow-hidden">
             <button 
               onClick={() => setActiveFilter("")}
               disabled={isFilterLoading}
               className={`px-3 py-2 text-xs font-medium disabled:opacity-50 disabled:cursor-not-allowed ${activeFilter === "" ? "bg-gray-100 text-gray-900" : "text-gray-500 hover:bg-gray-50"}`}
             >
               All
             </button>
             <button 
               onClick={() => setActiveFilter("new")}
               disabled={isFilterLoading}
               className={`px-3 py-2 text-xs font-medium border-l border-gray-200 disabled:opacity-50 disabled:cursor-not-allowed ${activeFilter === "new" ? "bg-gray-100 text-gray-900" : "text-gray-500 hover:bg-gray-50"}`}
             >
               New
             </button>
             <button 
               onClick={() => setActiveFilter("regressions")}
               disabled={isFilterLoading}
               className={`px-3 py-2 text-xs font-medium border-l border-gray-200 disabled:opacity-50 disabled:cursor-not-allowed ${activeFilter === "regressions" ? "bg-gray-100 text-gray-900" : "text-gray-500 hover:bg-gray-50"}`}
             >
               Regressions
             </button>
          </div>
        </div>
      </div>

      {/* ACTION BAR: Appears when items are selected */}
      {selectedIds.length > 0 && (
        <div className="bg-indigo-50 border border-indigo-100 p-3 rounded-lg flex justify-between items-center animate-in fade-in slide-in-from-top-2">
          <span className="text-sm font-semibold text-indigo-900 pl-2">
            {selectedIds.length} selected
          </span>
          <div className="flex gap-2">
            <button 
              onClick={() => resolveMutation.mutate(selectedIds)}
              disabled={resolveMutation.isPending || isFilterLoading}
              className="flex items-center gap-1.5 px-3 py-1.5 bg-white border border-indigo-200 text-indigo-700 text-xs font-medium rounded shadow-sm hover:bg-indigo-100 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <Check size={14} /> Resolve
            </button>
            <button 
              onClick={() => ignoreMutation.mutate(selectedIds)}
              disabled={ignoreMutation.isPending || isFilterLoading}
              className="flex items-center gap-1.5 px-3 py-1.5 bg-white border border-gray-300 text-gray-700 text-xs font-medium rounded shadow-sm hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <XCircle size={14} /> Ignore
            </button>
          </div>
        </div>
      )}

      <div className="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden relative">
        
        {/* Purple Progress Bar */}
        {isFilterLoading && (
           <div className="absolute top-0 left-0 w-full h-0.5 bg-purple-100 overflow-hidden z-10">
             <div 
               className="w-full h-full bg-purple-600" 
               style={{ animation: 'indeterminate-slide 1s infinite linear' }}
             ></div>
           </div>
        )}

        {/* Opacity Wrapper */}
        <div className={`transition-opacity duration-200 ${isFilterLoading ? 'opacity-50 pointer-events-none' : ''}`}>
          <table className="w-full text-left border-collapse">
            <thead>
              <tr className="bg-gray-50 border-b border-gray-200 text-xs uppercase text-gray-500 font-semibold">
                <th className="px-6 py-4 w-4">
                  <input 
                    type="checkbox" 
                    className="rounded border-gray-300 text-indigo-600 focus:ring-indigo-500"
                    onChange={handleSelectAll}
                    checked={!!(incidences && incidences.length > 0 && selectedIds.length === incidences.length)}
                  />
                </th>
                <th className="px-6 py-4">Incidence Details</th>
                <th className="px-6 py-4">Status</th>
                <th className="px-6 py-4 flex items-center gap-1">
                  Events <ArrowUpDown size={12} />
                </th>
                <th className="px-6 py-4">Users Affected</th>
                <th className="px-6 py-4 text-right">Last Seen</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {showSkeleton ? (
                // Render 5 Skeleton Rows with 6 columns
                Array.from({ length: 5 }).map((_, i) => (
                  <TableRowSkeleton key={i} cols={6} />
                ))
              ) : (
                // Render Real Data
                incidences?.map((incidence) => (
                  <tr 
                    key={incidence.id} 
                    className={`transition-colors group ${selectedIds.includes(incidence.id) ? "bg-indigo-50/40" : "hover:bg-slate-50/50"}`}
                  >
                    <td className="px-6 py-4">
                      <input 
                        type="checkbox" 
                        className="rounded border-gray-300 text-indigo-600 focus:ring-indigo-500"
                        checked={selectedIds.includes(incidence.id)}
                        onChange={() => handleSelectRow(incidence.id)}
                      />
                    </td>
                    <td className="px-6 py-4">
                      <Link to={`/incidences/${incidence.id}`} className="block group-hover:translate-x-1 transition-transform">
                        <div className="font-semibold text-gray-900 text-sm truncate max-w-lg">
                          {incidence.title}
                        </div>
                        <div className="text-xs text-gray-400 mt-1 font-mono">
                          ID: {incidence.id} • Fingerprint: {incidence.id * 732} {/* Simulating hash */}
                        </div>
                      </Link>
                    </td>
                    <td className="px-6 py-4">
                      <span className={`px-2 py-1 rounded text-[10px] font-bold uppercase tracking-wider ${
                        incidence.status === 'OPEN' ? 'bg-red-50 text-red-600 border border-red-100' : 
                        incidence.status === 'RESOLVED' ? 'bg-green-50 text-green-600 border border-green-100' :
                        'bg-gray-100 text-gray-600 border border-gray-200'
                      }`}>
                        {incidence.status}
                      </span>
                    </td>
                    <td className="px-6 py-4">
                      <div className="text-sm font-medium text-gray-700">
                        {incidence.occurrence_count.toLocaleString()}
                      </div>
                    </td>
                    <td className="px-6 py-4">
                      <div className="flex items-center gap-2 text-sm text-gray-600">
                        <User size={14} className="text-gray-400" />
                        {incidence.users_affected}
                      </div>
                    </td>
                    <td className="px-6 py-4 text-right">
                      <div className="text-sm text-gray-500">
                        {formatDistanceToNow(new Date(incidence.last_seen), { addSuffix: true })}
                      </div>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}