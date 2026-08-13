import React from "react";
import { Message } from "../../types";
import { User, Cpu } from "lucide-react";
import { motion } from "framer-motion";

interface ChatBubbleProps {
  message: Message;
}

export const ChatBubble: React.FC<ChatBubbleProps> = ({ message }) => {
  const isAssistant = message.role === "assistant";

  return (
    <motion.div
      initial={{ opacity: 0, y: 15 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3 }}
      className={`flex items-start gap-4 ${isAssistant ? "justify-start" : "justify-end"}`}
    >
      {/* Bot Icon */}
      {isAssistant && (
        <div className="w-9 h-9 rounded-xl bg-primary/10 border border-primary/20 flex items-center justify-center text-primary shrink-0">
          <Cpu size={18} />
        </div>
      )}

      {/* Bubble Container */}
      <div
        className={`max-w-[70%] p-4 rounded-2xl shadow-sm ${
          isAssistant
            ? "bg-card text-foreground border border-border/80 rounded-tl-none"
            : "bg-primary text-white rounded-tr-none shadow-md shadow-primary/10"
        }`}
      >
        {/* Author / Timestamp */}
        <div className="flex items-center justify-between gap-6 mb-1 text-[10px] opacity-70 font-semibold uppercase tracking-wider">
          <span>{isAssistant ? "AI Copilot" : "You"}</span>
          <span>{message.timestamp}</span>
        </div>

        {/* Message Content */}
        <p className="text-sm leading-relaxed whitespace-pre-wrap font-normal">
          {(() => {
            const regex = /(\*\*.*?\*\*)/g;
            const parts = message.content.split(regex);
            return parts.map((part, index) => {
              if (part.startsWith("**") && part.endsWith("**")) {
                return (
                  <strong key={index} className="font-bold">
                    {part.slice(2, -2)}
                  </strong>
                );
              }
              return part;
            });
          })()}
        </p>
      </div>

      {/* User Icon */}
      {!isAssistant && (
        <div className="w-9 h-9 rounded-full bg-secondary border border-border flex items-center justify-center text-muted-foreground shrink-0">
          <User size={18} />
        </div>
      )}
    </motion.div>
  );
};
