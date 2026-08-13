import React, { useState } from "react";
import { Send } from "lucide-react";
import { VoiceButton } from "../voice/VoiceButton";

interface ChatInputProps {
  onSendMessage: (text: string) => Promise<void>;
  disabled?: boolean;
}

export const ChatInput: React.FC<ChatInputProps> = ({ onSendMessage, disabled }) => {
  const [inputValue, setInputValue] = useState("");

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!inputValue.trim() || disabled) return;
    onSendMessage(inputValue);
    setInputValue("");
  };

  const handleTranscriptChange = (transcript: string) => {
    setInputValue(transcript);
  };

  const handleTranscriptFinal = (transcript: string) => {
    setInputValue(transcript);
  };

  return (
    <form
      onSubmit={handleSubmit}
      className="p-4 border-t border-border/80 bg-card/65 glass flex items-center gap-3"
    >
      {/* Real-time speech input controls */}
      <VoiceButton
        onTranscriptChange={handleTranscriptChange}
        onTranscriptFinal={handleTranscriptFinal}
      />

      <input
        type="text"
        value={inputValue}
        onChange={(e) => setInputValue(e.target.value)}
        disabled={disabled}
        placeholder="Type or use microphone to talk..."
        className="flex-1 h-11 px-4 bg-secondary/80 border border-border/60 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-primary/20 focus:border-primary text-foreground disabled:opacity-55"
      />

      <button
        type="submit"
        disabled={!inputValue.trim() || disabled}
        className="w-11 h-11 bg-primary text-white rounded-xl flex items-center justify-center hover:bg-primary/95 transition-all shadow-md shadow-primary/20 disabled:opacity-40 disabled:shadow-none shrink-0"
      >
        <Send size={16} />
      </button>
    </form>
  );
};
