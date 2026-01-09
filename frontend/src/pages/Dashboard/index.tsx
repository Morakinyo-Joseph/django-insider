import { useQuery } from "@tanstack/react-query";
import { fetchDashboardStats } from "../../api/client";
import { Activity, AlertTriangle, Users, Clock, CheckCircle } from "lucide-react";
import { Link } from "react-router-dom";

export default function Dashboard() {
  const { data, isLoading, error } = useQuery({
    queryKey: ["dashboardStats"],
    queryFn: fetchDashboardStats,
    refetchInterval: 30000, // Auto-refresh every 30 seconds
  });

  if (isLoading) return <div className="p-8">Loading dashboard...</div>;
  if (error) return <div className="p-8 text-red-600">Failed to load dashboard data.</div>;
  if (!data) return null;

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Dashboard</h1>
        <p className="text-gray-500">System health overview for the last 24 hours.</p>
      </div>

      {/* 1. HEALTH CARDS ROW */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        <StatsCard 
          label="Server Errors (500)" 
          value={data.velocity.errors_500} 
          icon={<AlertTriangle className="text-red-500" />} 
          trend="Last 24h"
          color="border-l-4 border-red-500"
        />
        <StatsCard 
          label="Client Errors (400)" 
          value={data.velocity.errors_400} 
          icon={<Activity className="text-yellow-500" />} 
          trend="Last 24h"
          color="border-l-4 border-yellow-500"
        />
        <StatsCard 
          label="Avg Latency" 
          value={`${data.health.avg_response_time_ms}ms`} 
          icon={<Clock className="text-blue-500" />} 
          trend="Global Avg"
          color="border-l-4 border-blue-500"
        />
        <StatsCard 
          label="Total Traffic" 
          value={data.velocity.total_24h} 
          icon={<CheckCircle className="text-green-500" />} 
          trend="Requests"
          color="border-l-4 border-green-500"
        />
      </div>

      {/* 2. TOP OFFENDERS SECTION */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200">
        <div className="px-6 py-4 border-b border-gray-100 flex justify-between items-center">
          <h2 className="text-lg font-semibold text-gray-800">Top Offenders</h2>
          <Link to="/incidences" className="text-sm text-indigo-600 hover:text-indigo-800 font-medium">
            View All Incidences &rarr;
          </Link>
        </div>
        
        <div className="overflow-x-auto">
          <table className="w-full text-left text-sm text-gray-600">
            <thead className="bg-gray-50 text-gray-900 uppercase font-medium text-xs">
              <tr>
                <th className="px-6 py-3">Incidence</th>
                <th className="px-6 py-3">Impact</th>
                <th className="px-6 py-3">Events</th>
                <th className="px-6 py-3">Status</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {data.top_offenders.length === 0 ? (
                <tr>
                  <td colSpan={4} className="px-6 py-8 text-center text-gray-400">
                    No active incidences found.
                  </td>
                </tr>
              ) : (
                data.top_offenders.map((incidence) => (
                  <tr key={incidence.id} className="hover:bg-gray-50 transition-colors">
                    <td className="px-6 py-4 font-medium text-gray-900 truncate max-w-md">
                      <Link to={`/incidences/${incidence.id}`} className="hover:underline">
                        {incidence.title}
                      </Link>
                    </td>
                    <td className="px-6 py-4">
                      <div className="flex items-center gap-2">
                        <Users size={16} className="text-gray-400" />
                        <span>{incidence.users_affected} Users</span>
                      </div>
                    </td>
                    <td className="px-6 py-4">{incidence.occurrence_count}</td>
                    <td className="px-6 py-4">
                      <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-red-100 text-red-800">
                        {incidence.status}
                      </span>
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

// Simple Helper Component for the Cards
function StatsCard({ label, value, icon, trend, color }: any) {
  return (
    <div className={`bg-white p-6 rounded-lg shadow-sm border border-gray-100 ${color}`}>
      <div className="flex justify-between items-start">
        <div>
          <p className="text-sm font-medium text-gray-500">{label}</p>
          <h3 className="text-2xl font-bold text-gray-900 mt-2">{value}</h3>
        </div>
        <div className="p-2 bg-gray-50 rounded-lg">{icon}</div>
      </div>
      <p className="text-xs text-gray-400 mt-4">{trend}</p>
    </div>
  );
}