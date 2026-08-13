import React from "react";
import { Link } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { ticketApi } from "../services/api/ticket";
import { assetApi } from "../services/api/asset";
import {
  Wrench,
  CheckCircle,
  AlertCircle,
  Clock,
  ArrowRight,
  TrendingUp,
} from "lucide-react";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
} from "recharts";

export const Dashboard: React.FC = () => {
  const { data: tickets = [] } = useQuery({
    queryKey: ["tickets"],
    queryFn: () => ticketApi.getTickets(),
  });

  const { data: assets = [] } = useQuery({
    queryKey: ["assets"],
    queryFn: () => assetApi.getAssets(),
  });

  // Analytics Metrics
  const openCount = tickets.filter((t) => t.status === "open").length;
  const inProgressCount = tickets.filter((t) => t.status === "in_progress").length;
  const closedCount = tickets.filter((t) => t.status === "closed" || t.status === "resolved").length;

  const priorityData = [
    { name: "Low", value: tickets.filter((t) => t.priority === "low").length },
    { name: "Medium", value: tickets.filter((t) => t.priority === "medium").length },
    { name: "High", value: tickets.filter((t) => t.priority === "high").length },
    { name: "Critical", value: tickets.filter((t) => t.priority === "critical").length },
  ];

  const statusData = [
    { name: "Open", value: openCount, color: "#3b82f6" },
    { name: "In Progress", value: inProgressCount, color: "#f59e0b" },
    { name: "Closed", value: closedCount, color: "#10b981" },
  ];


  return (
    <div className="p-6 space-y-6 overflow-y-auto h-full">
      {/* Welcome Banner */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 bg-gradient-to-r from-primary/10 to-blue-600/5 p-6 rounded-3xl border border-primary/10">
        <div>
          <h1 className="text-2xl font-bold text-foreground">Welcome Back, Field Tech</h1>
          <p className="text-sm text-muted-foreground mt-1">
            Analyze open workloads, locate assets, or speak to your AI Copilot to log status updates.
          </p>
        </div>
        <Link
          to="/chat"
          className="px-5 py-3 bg-primary text-white font-semibold rounded-2xl hover:bg-primary/95 transition-all shadow-md shadow-primary/25 flex items-center justify-center gap-2 self-start md:self-auto"
        >
          Open AI Copilot
          <ArrowRight size={16} />
        </Link>
      </div>

      {/* Telemetry metrics row */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-5">
        <div className="p-5 bg-card border border-border/80 rounded-2xl shadow-sm flex items-center gap-4">
          <div className="p-3 bg-primary/10 text-primary rounded-xl">
            <Wrench size={22} />
          </div>
          <div>
            <span className="text-xs font-semibold text-muted-foreground uppercase tracking-wider block">Total Assets</span>
            <span className="text-2xl font-bold text-foreground">{assets.length}</span>
          </div>
        </div>

        <div className="p-5 bg-card border border-border/80 rounded-2xl shadow-sm flex items-center gap-4">
          <div className="p-3 bg-blue-500/10 text-blue-600 rounded-xl">
            <AlertCircle size={22} />
          </div>
          <div>
            <span className="text-xs font-semibold text-muted-foreground uppercase tracking-wider block">Open Tickets</span>
            <span className="text-2xl font-bold text-foreground">{openCount}</span>
          </div>
        </div>

        <div className="p-5 bg-card border border-border/80 rounded-2xl shadow-sm flex items-center gap-4">
          <div className="p-3 bg-amber-500/10 text-amber-600 rounded-xl">
            <Clock size={22} />
          </div>
          <div>
            <span className="text-xs font-semibold text-muted-foreground uppercase tracking-wider block">In Progress</span>
            <span className="text-2xl font-bold text-foreground">{inProgressCount}</span>
          </div>
        </div>

        <div className="p-5 bg-card border border-border/80 rounded-2xl shadow-sm flex items-center gap-4">
          <div className="p-3 bg-emerald-500/10 text-emerald-600 rounded-xl">
            <CheckCircle size={22} />
          </div>
          <div>
            <span className="text-xs font-semibold text-muted-foreground uppercase tracking-wider block">Closed Tickets</span>
            <span className="text-2xl font-bold text-foreground">{closedCount}</span>
          </div>
        </div>
      </div>

      {/* Visual Analytics Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Ticket distribution bar chart */}
        <div className="lg:col-span-2 p-5 bg-card border border-border/80 rounded-2xl shadow-sm flex flex-col min-h-[300px]">
          <h3 className="text-sm font-bold text-foreground mb-4 flex items-center gap-2">
            <TrendingUp size={16} className="text-primary" />
            Ticket Priority Distribution
          </h3>
          <div className="flex-1 w-full min-h-[220px]">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={priorityData} margin={{ top: 10, right: 10, left: -25, bottom: 0 }}>
                <XAxis dataKey="name" stroke="#888888" fontSize={11} tickLine={false} axisLine={false} />
                <YAxis stroke="#888888" fontSize={11} tickLine={false} axisLine={false} />
                <Tooltip contentStyle={{ background: "hsl(var(--card))", border: "1px solid hsl(var(--border))", borderRadius: "8px" }} />
                <Bar dataKey="value" fill="hsl(var(--primary))" radius={[8, 8, 0, 0]} maxBarSize={45} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Ticket status pie chart */}
        <div className="p-5 bg-card border border-border/80 rounded-2xl shadow-sm flex flex-col min-h-[300px]">
          <h3 className="text-sm font-bold text-foreground mb-4">Ticket Status Breakdown</h3>
          <div className="flex-1 flex items-center justify-center min-h-[200px]">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  data={statusData}
                  cx="50%"
                  cy="50%"
                  innerRadius={60}
                  outerRadius={80}
                  paddingAngle={5}
                  dataKey="value"
                >
                  {statusData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.color} />
                  ))}
                </Pie>
                <Tooltip contentStyle={{ background: "hsl(var(--card))", border: "1px solid hsl(var(--border))", borderRadius: "8px" }} />
              </PieChart>
            </ResponsiveContainer>
          </div>
          <div className="flex items-center justify-center gap-4 mt-2 text-xs font-semibold">
            {statusData.map((entry) => (
              <div key={entry.name} className="flex items-center gap-1.5">
                <span className="w-2.5 h-2.5 rounded-full" style={{ backgroundColor: entry.color }} />
                <span className="text-muted-foreground">{entry.name}</span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};
