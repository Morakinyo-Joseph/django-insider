import { Outlet, NavLink } from "react-router-dom";
import { LayoutDashboard, Inbox, Settings } from "lucide-react";

export function DashboardLayout() {
  return (
    <div className="flex h-screen bg-gray-50 text-gray-900 font-sans">
      {/* SIDEBAR */}
      <aside className="w-64 bg-white border-r border-gray-200 flex flex-col">
        <div className="h-16 flex items-center px-6 border-b border-gray-100">
          <span className="text-xl font-bold text-indigo-600">Insider</span>
        </div>

        <nav className="flex-1 p-4 space-y-1">
          <NavItem to="/" icon={<LayoutDashboard size={20} />} label="Dashboard" />
          <NavItem to="/incidences" icon={<Inbox size={20} />} label="Incidence" />
          {/* We don't link to Detail/Forensics directly, they are hidden paths */}
        </nav>

        <div className="p-4 border-t border-gray-100">
          <NavItem to="/settings" icon={<Settings size={20} />} label="Settings" />
        </div>
      </aside>

      {/* MAIN CONTENT AREA */}
      <main className="flex-1 overflow-auto">
        <div className="p-8 max-w-7xl mx-auto">
          <Outlet /> {/* This is where the Page content is rendered */}
        </div>
      </main>
    </div>
  );
}

// Helper Component for Sidebar Links
function NavItem({ to, icon, label }: { to: string; icon: React.ReactNode; label: string }) {
  return (
    <NavLink
      to={to}
      className={({ isActive }) =>
        `flex items-center gap-3 px-3 py-2 rounded-md text-sm font-medium transition-colors ${
          isActive
            ? "bg-indigo-50 text-indigo-600"
            : "text-gray-600 hover:bg-gray-100 hover:text-gray-900"
        }`
      }
    >
      {icon}
      <span>{label}</span>
    </NavLink>
  );
}