import React, { useState, useEffect, useRef } from "react";
import { Mic, Square, Volume2 } from "lucide-react";
import toast from "react-hot-toast";

interface VoiceButtonProps {
  onTranscriptChange: (text: string) => void;
  onTranscriptFinal: (text: string) => void;
}

export const VoiceButton: React.FC<VoiceButtonProps> = ({
  onTranscriptChange,
  onTranscriptFinal,
}) => {
  const [isListening, setIsListening] = useState(false);
  const recognitionRef = useRef<any>(null);

  useEffect(() => {
    // Check browser speech recognition compatibility
    const SpeechRecognition =
      (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;

    if (SpeechRecognition) {
      const rec = new SpeechRecognition();
      rec.continuous = true;
      rec.interimResults = true;
      rec.lang = "en-US";

      rec.onresult = (event: any) => {
        let interimTranscript = "";
        let finalTranscript = "";

        for (let i = event.resultIndex; i < event.results.length; ++i) {
          if (event.results[i].isFinal) {
            finalTranscript += event.results[i][0].transcript;
          } else {
            interimTranscript += event.results[i][0].transcript;
          }
        }

        onTranscriptChange(interimTranscript || finalTranscript);
        if (finalTranscript) {
          onTranscriptFinal(finalTranscript);
        }
      };

      rec.onerror = (e: any) => {
        console.error("Speech Recognition Error:", e);
        if (e.error === "not-allowed") {
          toast.error("Microphone access blocked.");
        }
      };

      rec.onend = () => {
        setIsListening(false);
      };

      recognitionRef.current = rec;
    }
  }, [onTranscriptChange, onTranscriptFinal]);

  const toggleListening = () => {
    if (isListening) {
      if (recognitionRef.current) {
        recognitionRef.current.stop();
      }
    } else {
      if (recognitionRef.current) {
        try {
          recognitionRef.current.start();
          setIsListening(true);
        } catch (e) {
          console.error("Failed to start Speech Recognition:", e);
        }
      } else {
        toast.error("Speech Recognition is not supported in this browser. Please use a compatible browser like Google Chrome.");
      }
    }
  };

  return (
    <div className="flex items-center gap-3">
      {isListening && (
        <div className="flex items-center gap-1 h-6 px-2 bg-primary/10 rounded-full border border-primary/20 animate-pulse">
          <Volume2 size={12} className="text-primary" />
          <span className="text-[10px] font-semibold text-primary uppercase tracking-wider">Listening</span>
          {/* Simple waveform visualization */}
          <div className="flex gap-0.5 items-end h-3 ml-1">
            <span className="w-0.5 h-full bg-primary rounded-full bar-animation" style={{ animationDelay: "0.1s" }} />
            <span className="w-0.5 h-1/2 bg-primary rounded-full bar-animation" style={{ animationDelay: "0.3s" }} />
            <span className="w-0.5 h-3/4 bg-primary rounded-full bar-animation" style={{ animationDelay: "0.5s" }} />
            <span className="w-0.5 h-full bg-primary rounded-full bar-animation" style={{ animationDelay: "0.2s" }} />
          </div>
        </div>
      )}

      <button
        onClick={toggleListening}
        type="button"
        className={`w-11 h-11 rounded-xl flex items-center justify-center transition-all ${
          isListening
            ? "bg-destructive text-white hover:bg-destructive/95 shadow-md shadow-destructive/25 ring-2 ring-destructive ring-offset-2 dark:ring-offset-card"
            : "bg-primary text-white hover:bg-primary/95 shadow-md shadow-primary/25"
        }`}
        aria-label="Toggle Voice Control"
      >
        {isListening ? <Square size={18} /> : <Mic size={18} />}
      </button>
    </div>
  );
};
