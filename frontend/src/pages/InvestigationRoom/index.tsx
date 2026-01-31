import { useParams, Link } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { fetchIncidenceDetail, fetchIncidenceFootprints } from "../../api/client";
import { ChevronLeft, Clock, Globe, ShieldAlert, Terminal } from "lucide-react";
import { formatDistanceToNow } from "date-fns";
import type { StackFrame } from '../../types';
import { Skeleton } from "../../components/Skeleton";

export default function InvestigationRoom() {
  const { incidenceId } = useParams();

  // 1. Fetch Basic Incidence Info
  const { data: incidence, isLoading: isLoadingIncidence } = useQuery({
    queryKey: ["incidence", incidenceId],
    queryFn: () => fetchIncidenceDetail(incidenceId!),
  });

  // 2. Fetch Real Footprints (Samples)
  const { data: footprints, isLoading: isLoadingFootprints } = useQuery({
    queryKey: ["incidence", incidenceId, "footprints"],
    queryFn: () => fetchIncidenceFootprints(incidenceId!),
  });

  // SKELETON STATE
  if (isLoadingIncidence || isLoadingFootprints) {
    return (
      <div className="space-y-6">
        <div className="flex items-center gap-2 text-sm text-gray-500">
          <ChevronLeft size={16} /> <Skeleton className="h-4 w-24" />
        </div>

        {/* Header Skeleton */}
        <div className="bg-white p-6 rounded-xl border border-gray-200 shadow-sm flex justify-between items-start">
          <div className="space-y-2 w-full">
            <div className="flex items-center gap-3">
              <Skeleton className="h-5 w-16 rounded" /> {/* Status Badge */}
              <Skeleton className="h-8 w-1/3 rounded" /> {/* Title */}
            </div>
            <Skeleton className="h-4 w-48" /> {/* Fingerprint */}
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          
          {/* LEFT COLUMN: Stack Trace Skeleton */}
          <div className="lg:col-span-2 space-y-6">
            <div className="bg-slate-900 rounded-xl overflow-hidden border border-slate-800 flex flex-col h-[500px]">
              <div className="bg-slate-800 px-4 py-2 flex items-center gap-2">
                <Skeleton className="h-3 w-32 bg-slate-700" />
              </div>
              <div className="p-4 space-y-3">
                {/* Simulate code lines */}
                <Skeleton className="h-4 w-3/4 bg-slate-800" />
                <Skeleton className="h-4 w-1/2 bg-slate-800" />
                <Skeleton className="h-4 w-2/3 bg-slate-800" />
                <Skeleton className="h-4 w-full bg-slate-800" />
                <Skeleton className="h-4 w-5/6 bg-slate-800" />
              </div>
            </div>
          </div>

          {/* RIGHT COLUMN: Sidebar Skeleton */}
          <div className="space-y-6">
            
            {/* Context Card Skeleton */}
            <div className="bg-white p-5 rounded-xl border border-gray-200 shadow-sm space-y-4">
              <Skeleton className="h-4 w-24" /> {/* Header */}
              <div className="space-y-4">
                <div className="flex justify-between"><Skeleton className="h-4 w-20" /><Skeleton className="h-4 w-24" /></div>
                <div className="flex justify-between"><Skeleton className="h-4 w-20" /><Skeleton className="h-4 w-24" /></div>
                <div className="flex justify-between"><Skeleton className="h-4 w-20" /><Skeleton className="h-4 w-24" /></div>
              </div>
            </div>

            {/* List Skeleton */}
            <div className="bg-white rounded-xl border border-gray-200 shadow-sm overflow-hidden h-64">
              <div className="p-4 border-b border-gray-100 bg-gray-50/50 flex justify-between">
                 <Skeleton className="h-4 w-32" />
                 <Skeleton className="h-4 w-12" />
              </div>
              <div className="p-4 space-y-4">
                 <Skeleton className="h-10 w-full" />
                 <Skeleton className="h-10 w-full" />
                 <Skeleton className="h-10 w-full" />
              </div>
            </div>

          </div>
        </div>
      </div>
    );
  }

  if (!incidence) return <div className="p-8 text-red-600">Incidence not found.</div>;

  // 3. Simple Logic to find "Top" stats from the loaded footprints
  const topUser = footprints && footprints.length > 0 
    ? footprints[0].request_user 
    : "N/A";
    
  const lastPath = footprints && footprints.length > 0
    ? footprints[0].request_path
    : "Unknown Path";

  return (
    <div className="space-y-6">
      <Link to="/incidences" className="flex items-center gap-2 text-sm text-gray-500 hover:text-indigo-600 transition-colors">
        <ChevronLeft size={16} /> Back to Incidence
      </Link>

      {/* Header Section */}
      <div className="bg-white p-6 rounded-xl border border-gray-200 shadow-sm flex justify-between items-start">
        <div className="space-y-2">
          <div className="flex items-center gap-3">
            <span className={`text-[10px] font-bold px-2 py-0.5 rounded uppercase ${
               incidence.status === 'OPEN' ? 'bg-red-100 text-red-700' : 'bg-green-100 text-green-700'
            }`}>
              {incidence.status}
            </span>
            <h1 className="text-2xl font-bold text-gray-900">{incidence.title}</h1>
          </div>
          <p className="text-gray-500 font-mono text-sm">Fingerprint: {incidence.fingerprint || incidence.id}</p>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        
        {/* LEFT COLUMN: Stack Trace */}
        <div className="lg:col-span-2 space-y-6">
          <div className="bg-slate-900 rounded-xl overflow-hidden border border-slate-800 flex flex-col h-full">
            <div className="bg-slate-800 px-4 py-2 flex items-center gap-2 text-slate-300 text-xs font-mono">
              <Terminal size={14} /> stack_trace.log
            </div>
            
            <div className="flex-1 overflow-x-auto p-4">
              {/* LOGIC: Find the first footprint that HAS a stack trace */}
              {(() => {
                const traceSample = footprints?.find(fp => fp.stack_trace && fp.stack_trace.length > 0);
                
                if (!traceSample) {
                  return (
                    <div className="text-slate-500 text-sm font-mono p-4">
                      No stack trace captured in recent samples.
                    </div>
                  );
                }

                return (
                  <div className="space-y-1">
                    {traceSample?.stack_trace?.map((frame: StackFrame, index: number) => {
                      // Check if it is a system file (venv or site-packages)
                      const isSystemFile = frame.file.includes('site-packages') || frame.file.includes('venv');
                      
                      return (
                        <div key={index} className={`font-mono text-xs p-2 rounded border-l-2 ${
                          isSystemFile 
                            ? 'border-transparent text-slate-500 hover:bg-slate-800/30' 
                            : 'border-pink-500 bg-slate-800/50 text-slate-200'
                        }`}>
                          <div className="flex justify-between select-none">
                            <span className="truncate max-w-lg opacity-80">
                              {/* Show only the last 3 parts of the path for readability */}
                              {frame.file.split(/[/\\]/).slice(-3).join('/')}
                            </span>
                            <span className="opacity-50">Line {frame.line}</span>
                          </div>
                          
                          <div className="mt-1">
                             <span className="text-indigo-400">def {frame.function}</span>:
                          </div>
                          
                          <div className={`mt-1 pl-4 py-1 ${!isSystemFile ? 'text-pink-300 font-bold' : 'text-slate-400'}`}>
                            {frame.code}
                          </div>
                        </div>
                      );
                    })}
                  </div>
                );
              })()}
            </div>
            
            <div className="p-3 border-t border-slate-800 bg-slate-900 text-slate-500 text-xs">
               Exception raised at: <span className="text-slate-300">{lastPath}</span>
            </div>
          </div>
        </div>

        {/* RIGHT COLUMN: Sidebar Stats & Samples */}
        <div className="space-y-6">
          
          {/* Real Aggregates */}
          <div className="bg-white p-5 rounded-xl border border-gray-200 shadow-sm space-y-4">
            <h3 className="text-sm font-bold text-gray-900 uppercase tracking-tight">Context</h3>
            <div className="space-y-3">
              <EnvRow icon={<Globe size={14}/>} label="Last Path" value={lastPath} />
              <EnvRow icon={<ShieldAlert size={14}/>} label="Most Affected" value={topUser} />
              <EnvRow icon={<Clock size={14}/>} label="Last Seen" value={formatDistanceToNow(new Date(incidence.last_seen), { addSuffix: true })} />
            </div>
          </div>

          {/* Real Sample List */}
          <div className="bg-white rounded-xl border border-gray-200 shadow-sm overflow-hidden">
            <div className="p-4 border-b border-gray-100 bg-gray-50/50 flex justify-between items-center">
              <h3 className="text-sm font-bold text-gray-900 uppercase">Recent Footprints</h3>
              <span className="text-xs text-gray-500">{footprints?.length} found</span>
            </div>
            
            <div className="divide-y divide-gray-100 max-h-[400px] overflow-y-auto">
              {(!footprints || footprints.length === 0) ? (
                <div className="p-4 text-center text-gray-400 text-sm">No footprints found.</div>
              ) : (
                footprints.map((fp) => (
                  <Link 
                    key={fp.id} 
                    to={`/footprints/${fp.id}`} 
                    className="block p-4 hover:bg-indigo-50/30 transition-colors group"
                  >
                    <div className="flex justify-between text-xs mb-1">
                      <span className="font-mono text-indigo-600 font-semibold group-hover:underline">
                        {fp.request_id}
                      </span>
                      <span className="text-gray-400">
                        {formatDistanceToNow(new Date(fp.created_at))} ago
                      </span>
                    </div>
                    <div className="flex justify-between items-center">
                        <div className="text-[10px] text-gray-500 truncate max-w-[150px]">
                            {fp.request_user}
                        </div>
                        <span className={`text-[10px] px-1.5 py-0.5 rounded font-medium ${
                            fp.status_code >= 500 ? 'bg-red-100 text-red-700' : 'bg-green-100 text-green-700'
                        }`}>
                            {fp.status_code}
                        </span>
                    </div>
                  </Link>
                ))
              )}
            </div>
          </div>

        </div>
      </div>
    </div>
  );
}

// Helper UI Component
function EnvRow({ icon, label, value }: any) {
  return (
    <div className="flex justify-between items-center text-sm">
      <div className="flex items-center gap-2 text-gray-500">
        {icon} <span>{label}</span>
      </div>
      <span className="font-semibold text-gray-800 truncate max-w-[120px]" title={value}>{value}</span>
    </div>
  );
}