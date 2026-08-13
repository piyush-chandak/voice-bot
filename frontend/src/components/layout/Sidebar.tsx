import React, { useState } from "react";
import { Link, useLocation } from "react-router-dom";
import {
  LayoutDashboard,
  MessageSquare,
  Ticket,
  Package,
  ChevronLeft,
  ChevronRight,
  LogOut,
} from "lucide-react";
import { useAuth } from "../../contexts/AuthContext";

export const Sidebar: React.FC = () => {
  const [collapsed, setCollapsed] = useState(false);
  const location = useLocation();
  const { logout } = useAuth();

  const navItems = [
    { label: "Dashboard", icon: LayoutDashboard, path: "/" },
    { label: "AI Copilot", icon: MessageSquare, path: "/chat" },
    { label: "Tickets", icon: Ticket, path: "/tickets" },
    { label: "Assets", icon: Package, path: "/assets" },
    // { label: "Settings", icon: Settings, path: "/settings" },
  ];

  return (
    <aside
      className={`border-r border-border/80 bg-card transition-all duration-300 flex flex-col justify-between relative ${collapsed ? "w-16" : "w-64"
        }`}
    >
      <div>
        {/* Collapse button toggle */}
        <div className="h-16 flex items-center justify-end px-4 border-b border-border/50">
          <button
            onClick={() => setCollapsed(!collapsed)}
            className="p-1.5 hover:bg-secondary rounded-lg text-muted-foreground hover:text-foreground"
          >
            {collapsed ? <ChevronRight size={18} /> : <ChevronLeft size={18} />}
          </button>
        </div>

        {/* Navigation Items */}
        <nav className="p-3 space-y-1">
          {navItems.map((item) => {
            const isActive = location.pathname === item.path;
            const Icon = item.icon;
            return (
              <Link
                key={item.label}
                to={item.path}
                className={`flex items-center gap-3 px-2.5 py-2.5 rounded-xl text-sm font-medium transition-all ${isActive
                  ? "bg-primary text-white shadow-md shadow-primary/20"
                  : "text-muted-foreground hover:text-foreground hover:bg-secondary/80"
                  }`}
              >
                <Icon size={20} className="shrink-0" />
                {!collapsed && <span>{item.label}</span>}
              </Link>
            );
          })}
        </nav>
      </div>

      {/* Logout button at bottom */}
      <div className="p-3 border-t border-border/50">
        <button
          onClick={logout}
          className="w-full flex items-center gap-3 px-2.5 py-2.5 rounded-xl text-sm font-medium text-destructive hover:bg-destructive/10 transition-colors"
        >
          <LogOut size={20} className="shrink-0" />
          {!collapsed && <span>Logout</span>}
        </button>
      </div>
    </aside>
  );
};
