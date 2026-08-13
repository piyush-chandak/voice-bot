import React from "react";
import { useAuth } from "../../contexts/AuthContext";
import { useTheme } from "../../contexts/ThemeContext";
import { Sun, Moon } from "lucide-react";


export const Navbar: React.FC = () => {
  const { user } = useAuth();
  const { theme, toggleTheme } = useTheme();

  return (
    <header className="h-16 border-b border-border/80 glass px-6 flex items-center justify-between sticky top-0 z-40">
      {/* Brand Logo */}
      <div className="flex items-center gap-2">
        <div>
          <span className="font-bold tracking-tight text-lg bg-gradient-to-r from-primary to-blue-600 bg-clip-text text-transparent">
            TechBot
          </span>
          <span className="text-xs text-muted-foreground block -mt-1 font-medium">
            Technician Portal
          </span>
        </div>
      </div>

      {/* Actions / Profile */}
      <div className="flex items-center gap-4">
        {/* Toggle Theme */}
        <button
          onClick={toggleTheme}
          className="p-2 hover:bg-secondary rounded-lg transition-colors text-muted-foreground hover:text-foreground"
          aria-label="Toggle Theme"
        >
          {theme === "light" ? <Moon size={18} /> : <Sun size={18} />}
        </button>

        <div className="w-px h-6 bg-border" />

        {/* User Card */}
        <div className="flex items-center gap-3">
          <div className="w-9 h-9 rounded-full bg-primary/10 border border-primary/20 flex items-center justify-center text-primary font-bold">
            {user?.username?.substring(0, 2).toUpperCase() || "US"}
          </div>
          <div className="hidden sm:block text-left">
            <span className="text-sm font-semibold block text-foreground">
              {user?.username || "Technician"}
            </span>
            <span className="text-xs text-muted-foreground block -mt-0.5">
              {user?.email || "tech@company.com"}
            </span>
            <span className="text-xs text-muted-foreground block -mt-0.5">
              ({user?.role || "Guest"})
            </span>

          </div>
        </div>
      </div>
    </header>
  );
};
