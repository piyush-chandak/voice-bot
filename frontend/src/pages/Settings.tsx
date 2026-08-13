import React, { useState } from "react";
import { useTheme } from "../contexts/ThemeContext";
import { Sun, Moon, Volume2, Bell, Globe, Key } from "lucide-react";
import toast from "react-hot-toast";

export const Settings: React.FC = () => {
  const { theme, toggleTheme } = useTheme();
  const [provider, setProvider] = useState("whisper");
  const [notifications, setNotifications] = useState(true);

  const saveSettings = () => {
    toast.success("Settings updated successfully");
  };

  return (
    <div className="p-6 space-y-6 max-w-2xl overflow-y-auto h-full">
      <div>
        <h1 className="text-2xl font-bold text-foreground">Assistant Settings</h1>
        <p className="text-sm text-muted-foreground mt-0.5">
          Configure client defaults, themes, and audio providers.
        </p>
      </div>

      <div className="bg-card border border-border/80 rounded-2xl shadow-sm p-6 space-y-6">
        {/* Theme Settings */}
        <div className="flex items-center justify-between border-b border-border/50 pb-4">
          <div className="flex items-center gap-3">
            <div className="p-2.5 bg-primary/10 text-primary rounded-xl">
              {theme === "light" ? <Sun size={18} /> : <Moon size={18} />}
            </div>
            <div>
              <span className="font-semibold text-sm text-foreground block">App Appearance</span>
              <span className="text-xs text-muted-foreground block">
                Toggle between light and dark display modes.
              </span>
            </div>
          </div>
          <button
            onClick={toggleTheme}
            className="px-4 py-2 bg-secondary hover:bg-secondary/80 text-foreground font-semibold text-xs rounded-xl border border-border/80 transition-colors"
          >
            Use {theme === "light" ? "Dark Mode" : "Light Mode"}
          </button>
        </div>

        {/* Speech Provider */}
        <div className="flex items-center justify-between border-b border-border/50 pb-4">
          <div className="flex items-center gap-3">
            <div className="p-2.5 bg-primary/10 text-primary rounded-xl">
              <Volume2 size={18} />
            </div>
            <div>
              <span className="font-semibold text-sm text-foreground block">Voice STT Engine</span>
              <span className="text-xs text-muted-foreground block">
                Select your speech-to-text API provider.
              </span>
            </div>
          </div>
          <select
            value={provider}
            onChange={(e) => setProvider(e.target.value)}
            className="h-10 px-3 bg-secondary border border-border rounded-xl text-xs font-semibold focus:outline-none"
          >
            <option value="whisper">OpenAI Whisper</option>
            <option value="deepgram">Deepgram Nova-2</option>
          </select>
        </div>

        {/* Notifications */}
        <div className="flex items-center justify-between border-b border-border/50 pb-4">
          <div className="flex items-center gap-3">
            <div className="p-2.5 bg-primary/10 text-primary rounded-xl">
              <Bell size={18} />
            </div>
            <div>
              <span className="font-semibold text-sm text-foreground block">Desktop Alerts</span>
              <span className="text-xs text-muted-foreground block">
                Enable local system alert popups.
              </span>
            </div>
          </div>
          <button
            onClick={() => setNotifications(!notifications)}
            className={`px-4 py-2 text-xs font-semibold rounded-xl border transition-all ${notifications
                ? "bg-emerald-500/10 text-emerald-600 border-emerald-500/20"
                : "bg-secondary text-muted-foreground border-border"
              }`}
          >
            {notifications ? "Enabled" : "Disabled"}
          </button>
        </div>

        {/* System Language */}
        <div className="flex items-center justify-between border-b border-border/50 pb-4">
          <div className="flex items-center gap-3">
            <div className="p-2.5 bg-primary/10 text-primary rounded-xl">
              <Globe size={18} />
            </div>
            <div>
              <span className="font-semibold text-sm text-foreground block">Language Locale</span>
              <span className="text-xs text-muted-foreground block">
                Set default speech language recognition.
              </span>
            </div>
          </div>
          <select className="h-10 px-3 bg-secondary border border-border rounded-xl text-xs font-semibold focus:outline-none">
            <option value="en">English (US)</option>
            <option value="es">Español</option>
            <option value="de">Deutsch</option>
          </select>
        </div>

        {/* API keys config */}
        <div className="flex items-center justify-between pb-2">
          <div className="flex items-center gap-3">
            <div className="p-2.5 bg-primary/10 text-primary rounded-xl">
              <Key size={18} />
            </div>
            <div>
              <span className="font-semibold text-sm text-foreground block">API Key Integrations</span>
              <span className="text-xs text-muted-foreground block">
                Update third-party API configurations.
              </span>
            </div>
          </div>
          <button
            onClick={() => toast.error("Key management restricted to Administrators")}
            className="px-4 py-2 bg-secondary hover:bg-secondary/80 text-foreground font-semibold text-xs rounded-xl border border-border/80 transition-colors"
          >
            Configure Keys
          </button>
        </div>
      </div>

      <button
        onClick={saveSettings}
        className="w-full py-3 bg-primary text-white font-bold rounded-xl shadow-md shadow-primary/25 hover:bg-primary/95 transition-all"
      >
        Save Changes
      </button>
    </div>
  );
};
