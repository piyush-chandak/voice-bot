import React from "react";
import { useNavigate } from "react-router-dom";
import { Ticket } from "../../types";
import { CheckCircle, ExternalLink } from "lucide-react";

interface ChatTicketListProps {
  tickets: Ticket[];
  selectedTicketId?: number;
  onSelectTicket?: (ticket: Ticket) => void;
}

export const ChatTicketList: React.FC<ChatTicketListProps> = ({
  tickets,
  selectedTicketId,
  onSelectTicket,
}) => {
  const navigate = useNavigate();

  return (
    <div className="pl-12 pr-4 flex flex-wrap gap-3">
      {tickets.map((ticket) => {
        const isSelected = selectedTicketId === ticket.id;
        return (
          <div
            key={ticket.id}
            className={`p-4 rounded-2xl border text-left transition-all w-64 max-w-full flex flex-col justify-between ${
              isSelected
                ? "border-primary bg-primary/5 ring-1 ring-primary"
                : "border-border hover:border-muted-foreground/30 bg-card"
            }`}
          >
            <div>
              <div className="flex justify-between items-center mb-2">
                <span className="text-[10px] text-muted-foreground font-mono font-bold">
                  TICKET #{ticket.id}
                </span>
                <span
                  className={`px-2 py-0.5 rounded-full text-[10px] font-bold uppercase ${
                    ticket.priority === "critical" || ticket.priority === "high"
                      ? "bg-destructive/10 text-destructive"
                      : "bg-secondary text-foreground"
                  }`}
                >
                  {ticket.priority}
                </span>
              </div>
              <h4 className="font-bold text-sm text-foreground line-clamp-1">
                {ticket.title}
              </h4>
              <p className="text-xs text-muted-foreground mt-2 line-clamp-2">
                {ticket.description}
              </p>
              <div className="mt-3 flex items-center justify-between text-[11px] text-muted-foreground border-t border-border/30 pt-2">
                <span>
                  Status:{" "}
                  <b className="text-primary capitalize">
                    {ticket.status.replace("_", " ")}
                  </b>
                </span>
              </div>
            </div>

            <div className="mt-4 space-y-2">
              {onSelectTicket && (
                <button
                  onClick={() => onSelectTicket(ticket)}
                  className={`w-full py-2 rounded-xl text-xs font-bold transition-all flex items-center justify-center gap-1.5 ${
                    isSelected
                      ? "bg-emerald-500 text-white hover:bg-emerald-600"
                      : "bg-secondary text-foreground hover:bg-secondary/80 border border-border/80"
                  }`}
                >
                  {isSelected ? (
                    <>
                      <CheckCircle size={12} />
                      Active Ticket
                    </>
                  ) : (
                    "Select Ticket"
                  )}
                </button>
              )}

              <button
                onClick={() => navigate(`/tickets?id=${ticket.id}`)}
                className="w-full py-1.5 rounded-xl text-xs font-semibold text-primary hover:bg-primary/10 border border-primary/20 transition-all flex items-center justify-center gap-1"
              >
                <ExternalLink size={12} />
                View Ticket Details
              </button>
            </div>
          </div>
        );
      })}
    </div>
  );
};
