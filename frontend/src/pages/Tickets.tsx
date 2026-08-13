import React, { useState, useEffect } from "react";
import { useSearchParams } from "react-router-dom";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { ticketApi } from "../services/api/ticket";
import { Ticket } from "../types";
import { Search, Eye, CheckCircle2, Circle } from "lucide-react";
import toast from "react-hot-toast";

export const Tickets: React.FC = () => {
  const [searchParams] = useSearchParams();
  const targetId = searchParams.get("id");
  const queryClient = useQueryClient();
  const [searchTerm, setSearchTerm] = useState("");
  const [statusFilter, setStatusFilter] = useState("all");
  const [priorityFilter, setPriorityFilter] = useState("all");
  const [selectedTicket, setSelectedTicket] = useState<Ticket | null>(null);

  const { data: tickets = [], isLoading } = useQuery({
    queryKey: ["tickets"],
    queryFn: () => ticketApi.getTickets(),
  });

  useEffect(() => {
    if (targetId && tickets.length > 0) {
      const found = tickets.find((t) => t.id === parseInt(targetId, 10));
      if (found) {
        setSelectedTicket(found);
      }
    }
  }, [targetId, tickets]);


  const updateMutation = useMutation({
    mutationFn: ({ id, status }: { id: number; status: string }) =>
      ticketApi.updateTicket(id, { status }),
    onSuccess: (updated) => {
      queryClient.invalidateQueries({ queryKey: ["tickets"] });
      setSelectedTicket(updated);
      toast.success("Ticket status updated successfully");
    },
    onError: (error: any) => {
      const msg = error?.response?.data?.detail || "Failed to update ticket";
      toast.error(msg);
    },
  });

  const filteredTickets = tickets.filter((ticket) => {
    const matchesSearch =
      ticket.title.toLowerCase().includes(searchTerm.toLowerCase()) ||
      ticket.description.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesStatus = statusFilter === "all" || ticket.status === statusFilter;
    const matchesPriority = priorityFilter === "all" || ticket.priority === priorityFilter;

    return matchesSearch && matchesStatus && matchesPriority;
  });

  return (
    <div className="p-6 space-y-6 flex-1 flex flex-col min-h-0">
      {/* Header */}
      <div className="flex items-center justify-between shrink-0">
        <div>
          <h1 className="text-2xl font-bold text-foreground">Maintenance Tickets</h1>
          <p className="text-sm text-muted-foreground mt-0.5">
            Audit reported breakdowns, modify workflow status, or log actions.
          </p>
        </div>
      </div>

      {/* Filters row */}
      <div className="flex flex-col md:flex-row gap-4 shrink-0 bg-card p-4 rounded-2xl border border-border/80 shadow-sm">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-2.5 text-muted-foreground" size={16} />
          <input
            type="text"
            placeholder="Search tickets by keyword..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-full h-10 pl-10 pr-4 bg-secondary/80 border border-border/60 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-primary/20"
          />
        </div>

        <div className="flex flex-wrap gap-3">
          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="h-10 px-3 bg-secondary/80 border border-border/60 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-primary/20 text-muted-foreground font-semibold"
          >
            <option value="all">All Statuses</option>
            <option value="open">Open</option>
            <option value="in_progress">In Progress</option>
            <option value="completed">Completed</option>
          </select>

          <select
            value={priorityFilter}
            onChange={(e) => setPriorityFilter(e.target.value)}
            className="h-10 px-3 bg-secondary/80 border border-border/60 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-primary/20 text-muted-foreground font-semibold"
          >
            <option value="all">All Priorities</option>
            <option value="low">Low</option>
            <option value="medium">Medium</option>
            <option value="high">High</option>
            <option value="critical">Critical</option>
          </select>
        </div>
      </div>

      {/* Main grid with table & details side-by-side if selected */}
      <div className="flex-1 flex gap-6 min-h-0">
        <div className="flex-1 bg-card rounded-2xl border border-border/80 shadow-sm overflow-hidden flex flex-col">
          <div className="overflow-y-auto flex-1">
            {isLoading ? (
              <div className="p-8 text-center text-sm text-muted-foreground">Loading tickets...</div>
            ) : filteredTickets.length === 0 ? (
              <div className="p-8 text-center text-sm text-muted-foreground">No matching tickets found.</div>
            ) : (
              <table className="w-full text-left border-collapse">
                <thead className="bg-secondary/40 border-b border-border text-xs font-bold text-muted-foreground uppercase tracking-wider sticky top-0">
                  <tr>
                    <th className="p-4">Ticket</th>
                    <th className="p-4">Asset</th>
                    <th className="p-4">Priority</th>
                    <th className="p-4">Status</th>
                    <th className="p-4 text-right">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-border/60 text-sm">
                  {filteredTickets.map((t) => (
                    <tr key={t.id} className="hover:bg-secondary/20 transition-all">
                      <td className="p-4">
                        <span className="font-semibold text-foreground block">{t.title}</span>
                        <span className="text-[10px] text-muted-foreground font-mono block">#{t.id}</span>
                      </td>
                      <td className="p-4">
                        <span className="font-medium text-foreground">{t.asset?.name || "Asset"}</span>
                        <span className="text-xs text-muted-foreground block font-mono">{t.asset?.sku}</span>
                      </td>
                      <td className="p-4">
                        <span
                          className={`px-2 py-0.5 rounded-full text-xs font-bold uppercase ${
                            t.priority === "critical" || t.priority === "high"
                              ? "bg-red-500/10 text-red-600"
                              : "bg-blue-500/10 text-blue-600"
                          }`}
                        >
                          {t.priority}
                        </span>
                      </td>
                      <td className="p-4">
                        <div className="flex items-center gap-1.5 font-medium">
                          {t.status === "completed" || t.status === "closed" ? (
                            <CheckCircle2 size={16} className="text-emerald-500" />
                          ) : t.status === "in_progress" ? (
                            <Circle size={16} className="text-amber-500 fill-amber-500/20" />
                          ) : (
                            <Circle size={16} className="text-blue-500" />
                          )}
                          <span className="capitalize">{t.status.replace("_", " ")}</span>
                        </div>
                      </td>
                      <td className="p-4 text-right">
                        <button
                          onClick={() => setSelectedTicket(t)}
                          className="p-1.5 hover:bg-secondary rounded-lg text-muted-foreground hover:text-foreground"
                        >
                          <Eye size={16} />
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </div>
        </div>

        {/* Selected Ticket details drawer */}
        {selectedTicket && (
          <div className="w-96 bg-card border border-border/80 rounded-2xl shadow-lg p-5 flex flex-col justify-between shrink-0 animate-in slide-in-from-right duration-200">
            <div className="space-y-5">
              <div className="flex items-center justify-between border-b border-border/50 pb-3">
                <div>
                  <span className="text-[10px] text-muted-foreground font-mono font-bold block">TICKET #{selectedTicket.id}</span>
                  <h3 className="font-bold text-foreground text-base mt-0.5">{selectedTicket.title}</h3>
                </div>
                <button
                  onClick={() => setSelectedTicket(null)}
                  className="px-2.5 py-1 text-xs hover:bg-secondary rounded-lg font-medium text-muted-foreground"
                >
                  Close
                </button>
              </div>

              <div>
                <span className="text-xs text-muted-foreground font-semibold">Description</span>
                <p className="text-sm text-foreground mt-1 bg-secondary/30 p-3 rounded-xl border border-border/40">
                  {selectedTicket.description}
                </p>
              </div>

              {selectedTicket.asset && (
                <div>
                  <span className="text-xs text-muted-foreground font-semibold">Asset Detail</span>
                  <div className="mt-1 bg-secondary/20 p-3 rounded-xl border border-border/30 text-xs">
                    <p className="font-bold text-foreground">{selectedTicket.asset.name}</p>
                    <p className="font-mono text-muted-foreground mt-0.5">{selectedTicket.asset.sku}</p>
                  </div>
                </div>
              )}

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <span className="text-xs text-muted-foreground font-semibold">Priority</span>
                  <span className="block text-sm font-bold text-foreground uppercase mt-0.5">{selectedTicket.priority}</span>
                </div>
                <div>
                  <span className="text-xs text-muted-foreground font-semibold">Current Status</span>
                  <span className="block text-sm font-bold text-foreground capitalize mt-0.5">{selectedTicket.status.replace("_", " ")}</span>
                </div>
              </div>
            </div>

            {/* Action buttons */}
            <div className="border-t border-border/50 pt-4 flex gap-3">
              {selectedTicket.status !== "in_progress" && selectedTicket.status !== "completed" && selectedTicket.status !== "closed" && (
                <button
                  onClick={() => updateMutation.mutate({ id: selectedTicket.id, status: "in_progress" })}
                  className="flex-1 py-2 bg-amber-500 hover:bg-amber-600 text-white font-semibold text-xs rounded-xl shadow-md shadow-amber-500/10"
                >
                  Start Work
                </button>
              )}
              {selectedTicket.status !== "completed" && selectedTicket.status !== "closed" && (
                <button
                  onClick={() => updateMutation.mutate({ id: selectedTicket.id, status: "completed" })}
                  className="flex-1 py-2 bg-emerald-500 hover:bg-emerald-600 text-white font-semibold text-xs rounded-xl shadow-md shadow-emerald-500/10"
                >
                  Complete Ticket
                </button>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
