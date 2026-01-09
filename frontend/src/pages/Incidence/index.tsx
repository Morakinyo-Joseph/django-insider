import { useQuery } from "@tanstack/react-query";
import { fetchIncidences } from "../../api/client";
import { Search, Filter, ArrowUpDown, User } from "lucide-react";
import { Link } from "react-router-dom";
import { formatDistanceToNow } from "date-fns";

export default function Incidence() {
  const { data: incidences, isLoading } = useQuery({
    queryKey: ["incidences"],
    queryFn: fetchIncidences,
  });

  if (isLoading) return <div className="p-8 text-gray-500">Loading incidences...</div>;

  return (
    <div className="space-y-6">
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
          <button className="flex items-center gap-2 px-4 py-2 border border-gray-200 rounded-lg text-sm font-medium hover:bg-gray-50">
            <Filter size={16} />
            Filter
          </button>
        </div>
      </div>

      <div className="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden">
        <table className="w-full text-left border-collapse">
          <thead>
            <tr className="bg-gray-50 border-b border-gray-200 text-xs uppercase text-gray-500 font-semibold">
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
            {incidences?.map((incidence) => (
              <tr key={incidence.id} className="hover:bg-slate-50/50 transition-colors group">
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
                    incidence.status === 'OPEN' ? 'bg-red-50 text-red-600 border border-red-100' : 'bg-green-50 text-green-600 border border-green-100'
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
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}