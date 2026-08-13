import React, { useEffect, useRef, useState } from "react";
import { useChat } from "../contexts/ChatContext";
import { ChatBubble } from "../components/chat/ChatBubble";
import { ChatInput } from "../components/chat/ChatInput";
import { ConfirmationDialog } from "../components/common/ConfirmationDialog";
import {
  RotateCcw,
  Phone,
  PhoneOff,
  Volume2,
  VolumeX
} from "lucide-react";
import { LiveKitRoom, RoomAudioRenderer } from "@livekit/components-react";
import { chatApi } from "../services/api/chat";
import { Message } from "../types";
import toast from "react-hot-toast";

export const Chat: React.FC = () => {
  const {
    messages,
    sendMessage,
    isTyping,
    locationStatus,
    submitManualLocation,
    resetChat,
    ttsEnabled,
    setTtsEnabled,
    location,
    sessionId
  } = useChat();

  const [isManualLocationOpen, setIsManualLocationOpen] = useState(false);
  const [callActive, setCallActive] = useState(false);
  const [lkToken, setLkToken] = useState("");
  const [lkUrl, setLkUrl] = useState("");

  const scrollRef = useRef<HTMLDivElement>(null);


  // Auto-scroll on new messages
  useEffect(() => {
    scrollRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, isTyping]);

  // Open manual location dialog if browser coordinates access was explicitly denied
  useEffect(() => {
    if (locationStatus === "denied") {
      setIsManualLocationOpen(true);
    }
  }, [locationStatus]);

  return (
    <div className="flex flex-1 h-full min-h-0 bg-secondary/5 relative justify-center">
      {/* Centered ChatGPT/Claude-like Chat Layout */}
      <div className="flex-1 max-w-4xl flex flex-col min-h-0 bg-card border-x border-border/80 shadow-lg">

        <div className="h-16 border-b border-border/80 bg-card px-6 flex items-center justify-between shrink-0 shadow-sm">
          <div>
            <h2 className="font-bold text-sm text-foreground flex items-center gap-2">
              Voice Technician Assistant
              {callActive && (
                <div className="flex items-center gap-0.5 h-4 px-1.5 bg-emerald-500/10 border border-emerald-500/20 rounded-full">
                  <span className="w-1 h-2 bg-emerald-500 rounded-full animate-bounce" style={{ animationDelay: "0.1s" }} />
                  <span className="w-1 h-3 bg-emerald-500 rounded-full animate-bounce" style={{ animationDelay: "0.3s" }} />
                  <span className="w-1 h-1.5 bg-emerald-500 rounded-full animate-bounce" style={{ animationDelay: "0.5s" }} />
                </div>
              )}
            </h2>
            <span className="text-[10px] text-muted-foreground font-semibold block -mt-0.5 uppercase tracking-wider">
              Copilot Session: {location ? `${location.latitude.toFixed(4)}, ${location.longitude.toFixed(4)}` : "Awaiting GPS"}
            </span>
          </div>

          <div className="flex items-center gap-3">
            {callActive ? (
              <span className="h-9 px-3 bg-emerald-500/10 border border-emerald-500/25 text-emerald-500 text-xs font-bold rounded-xl flex items-center gap-1.5">
                <span className="h-1.5 w-1.5 rounded-full bg-emerald-500 animate-pulse" />
                Voice Active
              </span>
            ) : (
              <button
                onClick={async () => {
                  toast.loading("Requesting location permission...", { id: "lk-dial" });

                  let lat: number | undefined = undefined;
                  let lon: number | undefined = undefined;

                  const getCoords = (): Promise<{lat: number, lon: number} | null> => {
                    return new Promise((resolve) => {
                      if (location && location.latitude && location.longitude) {
                        resolve({ lat: location.latitude, lon: location.longitude });
                      } else if (navigator.geolocation) {
                        navigator.geolocation.getCurrentPosition(
                          (position) => {
                            resolve({
                              lat: position.coords.latitude,
                              lon: position.coords.longitude
                            });
                          },
                          (err) => {
                            console.warn("Browser geolocation rejected or failed:", err);
                            resolve(null);
                          },
                          { enableHighAccuracy: true, timeout: 5000, maximumAge: 0 }
                        );
                      } else {
                        resolve(null);
                      }
                    });
                  };

                  const coords = await getCoords();

                  if (coords) {
                    lat = coords.lat;
                    lon = coords.lon;
                    await submitManualLocation(lat, lon); // Cache in context & localStorage
                  } else {
                    toast.dismiss("lk-dial");
                    toast.error("Location permission denied. Please enter coordinates manually to start the call.", { duration: 5000 });
                    setIsManualLocationOpen(true);
                    return;
                  }

                  toast.loading("Initiating Voice agent session...", { id: "lk-dial" });
                  try {
                    const roomName = `room-${sessionId}`;
                    const response = await chatApi.getLivekitToken(roomName, sessionId, lat, lon);
                    setLkToken(response.token);
                    setLkUrl(response.url);
                    setCallActive(true);
                    toast.dismiss("lk-dial");
                    toast.success("Voice Agent Connected!");
                  } catch (e) {
                    toast.dismiss("lk-dial");
                    toast.error("Failed to connect to LiveKit voice agent");
                  }
                }}
                className="h-9 px-3 bg-emerald-500 hover:bg-emerald-600 text-white text-xs font-bold rounded-xl flex items-center gap-1.5 hover:scale-105 active:scale-95 transition-all shadow-md"
              >
                <Phone size={14} />
                Connect Voice
              </button>
            )}

            <button
              onClick={() => setTtsEnabled(!ttsEnabled)}
              className={`p-2 rounded-lg transition-colors flex items-center gap-1.5 text-xs font-semibold ${ttsEnabled ? "bg-primary/20 text-primary" : "hover:bg-secondary text-muted-foreground"
                }`}
              title="Toggle Text-to-Speech"
            >
              {ttsEnabled ? <Volume2 size={15} /> : <VolumeX size={15} />}
              TTS {ttsEnabled ? "ON" : "OFF"}
            </button>

            <button
              onClick={resetChat}
              className="p-2 hover:bg-secondary rounded-lg text-muted-foreground hover:text-foreground transition-colors flex items-center gap-1.5 text-xs font-semibold"
              title="Reset Chat Session"
            >
              <RotateCcw size={14} />
              Reset
            </button>
          </div>
        </div>

        <div className="flex-1 overflow-y-auto p-6 space-y-4">
          {messages.map((msg: Message) => (
            <ChatBubble key={msg.id} message={msg} />
          ))}

          {isTyping && (
            <div className="flex items-center gap-3 justify-start">
              <div className="w-9 h-9 rounded-xl bg-primary/10 border border-primary/20 flex items-center justify-center text-primary shrink-0 animate-pulse">
                AI
              </div>
              <div className="bg-card border border-border/80 px-4 py-3 rounded-2xl rounded-tl-none shadow-sm flex items-center gap-1">
                <span className="w-1.5 h-1.5 bg-muted-foreground rounded-full animate-bounce" style={{ animationDelay: "0.1s" }} />
                <span className="w-1.5 h-1.5 bg-muted-foreground rounded-full animate-bounce" style={{ animationDelay: "0.3s" }} />
                <span className="w-1.5 h-1.5 bg-muted-foreground rounded-full animate-bounce" style={{ animationDelay: "0.5s" }} />
              </div>
            </div>
          )}

          <div ref={scrollRef} />
        </div>

        {/* Chat input box at the bottom of left pane */}
        <div className="p-4 bg-card border-t border-border/80 shrink-0">
          <ChatInput onSendMessage={(text: string) => sendMessage(text)} disabled={isTyping} />
        </div>

      </div>

      {callActive && lkToken && lkUrl && (
        <LiveKitRoom
          video={false}
          audio={true}
          token={lkToken}
          serverUrl={lkUrl}
          connect={true}
          onDisconnected={() => {
            setCallActive(false);
            setLkToken("");
            toast.error("Call ended");
          }}
        >
          <RoomAudioRenderer />
        </LiveKitRoom>
      )}

      {/* Small floating call window with sound waves */}
      {callActive && (
        <div className="fixed bottom-24 right-8 bg-slate-950 border border-slate-800 text-white rounded-2xl shadow-2xl p-4 flex flex-col items-center gap-3 w-64 animate-in fade-in slide-in-from-bottom-5 duration-200 z-50">
          <div className="flex items-center justify-between w-full border-b border-slate-800 pb-2">
            <span className="text-xs font-bold text-slate-300 flex items-center gap-1.5">
              <span className="h-2 w-2 rounded-full bg-emerald-500 animate-ping" />
              Live Voice Bridge
            </span>
            <span className="text-[10px] text-emerald-400 font-bold uppercase tracking-wider">
              Connected
            </span>
          </div>
          
          <div className="h-14 flex items-center justify-center gap-1">
            <span className="w-1.5 h-6 bg-emerald-500 rounded-full animate-bounce" style={{ animationDelay: "0.1s" }} />
            <span className="w-1.5 h-10 bg-emerald-500 rounded-full animate-bounce" style={{ animationDelay: "0.3s" }} />
            <span className="w-1.5 h-8 bg-emerald-500 rounded-full animate-bounce" style={{ animationDelay: "0.5s" }} />
            <span className="w-1.5 h-12 bg-emerald-500 rounded-full animate-bounce" style={{ animationDelay: "0.2s" }} />
            <span className="w-1.5 h-6 bg-emerald-500 rounded-full animate-bounce" style={{ animationDelay: "0.4s" }} />
          </div>

          <button
            onClick={() => {
              setCallActive(false);
              setLkToken("");
              toast.error("Call ended");
            }}
            className="w-full py-2 bg-red-500 hover:bg-red-600 active:scale-95 text-white font-bold text-xs rounded-xl flex items-center justify-center gap-1.5 transition-all shadow-lg"
          >
            <PhoneOff size={14} />
            End Call
          </button>
        </div>
      )}

      {/* Manual coordinates input modal */}
      <ConfirmationDialog
        isOpen={isManualLocationOpen}
        onClose={() => setIsManualLocationOpen(false)}
        onSubmit={submitManualLocation}
      />
    </div>
  );
};
