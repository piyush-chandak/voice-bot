import React, { createContext, useContext, useState, useEffect } from "react";
import { Message, Asset, Ticket } from "../types";
import { chatApi } from "../services/api/chat";
import { locationApi } from "../services/api/location";
import { ticketApi } from "../services/api/ticket";
import { assetApi } from "../services/api/asset";

import toast from "react-hot-toast";

interface ChatContextType {
  messages: Message[];
  selectedAsset: Asset | null;
  location: { latitude: number; longitude: number } | null;
  locationStatus: "idle" | "requesting" | "granted" | "denied";
  nearbyAssets: Asset[];
  currentTicketSummary: Partial<Ticket> | null;
  isTyping: boolean;
  sessionId: string;
  ttsEnabled: boolean;
  setTtsEnabled: (enabled: boolean) => void;
  sendMessage: (text: string, selectedAssetId?: number) => Promise<void>;
  sendVoiceMessage: (audioBlob: Blob) => Promise<void>;
  identifyAssetFromFrame: (imageBlob: Blob) => Promise<void>;
  setSelectedAsset: (asset: Asset | null) => Promise<void>;
  requestLocation: () => Promise<void>;
  submitManualLocation: (lat: number, lon: number) => Promise<void>;
  confirmCreateTicket: () => Promise<void>;
  resetChat: () => void;
}

const ChatContext = createContext<ChatContextType | undefined>(undefined);

export const ChatProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [messages, setMessages] = useState<Message[]>([]);
  const [selectedAsset, setSelectedAssetState] = useState<Asset | null>(null);
  const [location, setLocation] = useState<{ latitude: number; longitude: number } | null>(() => {
    const cached = localStorage.getItem("technician_location");
    if (cached) {
      try {
        return JSON.parse(cached);
      } catch (e) {
        return null;
      }
    }
    return null;
  });
  const [locationStatus, setLocationStatus] = useState<"idle" | "requesting" | "granted" | "denied">(() => {
    return localStorage.getItem("technician_location") ? "granted" : "idle";
  });
  const [nearbyAssets, setNearbyAssets] = useState<Asset[]>([]);
  const [currentTicketSummary, setCurrentTicketSummary] = useState<Partial<Ticket> | null>(null);
  const [isTyping, setIsTyping] = useState<boolean>(false);
  const [sessionId, setSessionId] = useState<string>("");
  const [ttsEnabled, setTtsEnabled] = useState<boolean>(false);

  useEffect(() => {
    // Generate a unique session ID for this chat session
    const id = `session-${Math.random().toString(36).substr(2, 9)}`;
    setSessionId(id);
    // Seed initial assistant greeting
    setMessages([
      {
        id: "msg-init",
        role: "assistant",
        content: "Hello! I am your AI Assistant. Let's get started. May I access your browser location to locate nearby assets?",
        timestamp: new Date().toLocaleTimeString(),
      },
    ]);

    // Poll current session state from the backend (every 2 seconds) to keep the chat logs updated with voice agent
    const interval = setInterval(async () => {
      if (!id) return;
      try {
        const state = await chatApi.getVoiceSessionState(id);
        if (state && state.messages && state.messages.length > 0) {
          // Sync messages
          setMessages((prev) => {
            // Keep the very first greeting
            const first = prev[0] ? [prev[0]] : [];
            const fresh = state.messages.map((m: any) => ({
              id: m.id || `msg-${Math.random()}`,
              role: m.role,
              content: m.content,
              timestamp: m.timestamp || new Date().toLocaleTimeString(),
              intent: m.id === state.messages[state.messages.length - 1].id ? state.intent : undefined,
              data: m.id === state.messages[state.messages.length - 1].id ? state.data : undefined,
            }));
            return [...first, ...fresh];
          });
        }
        if (state && state.nearby_assets && state.nearby_assets.length > 0) {
          setNearbyAssets(state.nearby_assets);
        }
        if (state && state.selected_asset_id) {
          const matched = (state.nearby_assets || []).find((a: any) => a.id === state.selected_asset_id);
          if (matched) {
            setSelectedAssetState(matched);
          }
        }
      } catch (e) {
        // quiet fail on background polling
      }
    }, 2000);

    return () => clearInterval(interval);
  }, []);

  const speakText = (text: string) => {
    if (!ttsEnabled || !("speechSynthesis" in window)) return;
    window.speechSynthesis.cancel();
    const cleanText = text.replace(/[*#`_\-]/g, "").trim();
    const utterance = new SpeechSynthesisUtterance(cleanText);
    window.speechSynthesis.speak(utterance);
  };

  const addMessage = (
    role: "user" | "assistant" | "tool",
    content: string,
    intent?: string,
    data?: any
  ) => {
    const newMsg: Message = {
      id: `msg-${Math.random().toString(36).substr(2, 9)}`,
      role,
      content,
      timestamp: new Date().toLocaleTimeString(),
      intent,
      data,
    };
    setMessages((prev) => [...prev, newMsg]);

    if (role === "assistant") {
      speakText(content);
    }
    return newMsg;
  };

  const pendingMessageRef = React.useRef<string>("");

  const requestLocation = async () => {
    setLocationStatus("requesting");
    if (!navigator.geolocation) {
      toast.error("Geolocation is not supported by your browser");
      setLocationStatus("denied");
      return;
    }

    navigator.geolocation.getCurrentPosition(
      async (position) => {
        const { latitude, longitude } = position.coords;
        await handleLocationSuccess(latitude, longitude);
      },
      (error) => {
        console.error("Location access error:", error);
        toast.error("Location permission denied. Please enter coordinates manually.");
        setLocationStatus("denied");
        addMessage(
          "assistant",
          "I couldn't access your location automatically. Could you please enable location services in your browser, or type in your coordinates manually using the dialog?"
        );
      }
    );
  };

  const handleLocationSuccess = async (lat: number, lon: number) => {
    setLocation({ latitude: lat, longitude: lon });
    setLocationStatus("granted");
    localStorage.setItem("technician_location", JSON.stringify({ latitude: lat, longitude: lon }));

    // Save to backend
    try {
      await locationApi.saveLocation({ latitude: lat, longitude: lon });
    } catch (e) {
      console.error("Failed saving location to server:", e);
    }

    const textToSend = pendingMessageRef.current;
    addMessage(
      "assistant",
      `Location confirmed: Latitude ${lat.toFixed(4)}, Longitude ${lon.toFixed(4)}.`
    );

    if (textToSend) {
      pendingMessageRef.current = "";
      setIsTyping(true);
      try {
        addMessage("user", textToSend);

        const response = await chatApi.sendChatMessage({
          message: textToSend,
          session_id: sessionId,
          latitude: lat,
          longitude: lon,
        });

        addMessage(
          "assistant",
          response.response,
          response.intent,
          response.data
        );

        if (response.data && response.data.type === "assets" && response.data.items) {
          setNearbyAssets(response.data.items);
        }
        if (response.selected_asset_id && !selectedAsset) {
          const items = response.data?.items || [];
          const found = items.find((a: any) => a.id === response.selected_asset_id);
          if (found) setSelectedAssetState(found);
        }
      } catch (e) {
        toast.error("Failed to process request with coordinates");
      } finally {
        setIsTyping(false);
      }
    } else {
      addMessage("assistant", "How can I help you with your assets or tickets today?");
    }
  };

  const submitManualLocation = async (lat: number, lon: number) => {
    await handleLocationSuccess(lat, lon);
  };

  const setSelectedAsset = async (asset: Asset | null) => {
    setSelectedAssetState(asset);
    if (asset) {
      // Trigger a dynamic LLM greeting response by posting a message to the backend
      await sendMessage(`I have selected the asset **${asset.name}** (${asset.sku}).`, asset.id);
    }
  };

  const sendMessage = async (text: string, selectedAssetId?: number) => {
    if (!text.trim()) return;

    addMessage("user", text);
    setIsTyping(true);

    try {
      const response = await chatApi.sendChatMessage({
        message: text,
        session_id: sessionId,
        latitude: location?.latitude,
        longitude: location?.longitude,
        selected_asset_id: selectedAssetId !== undefined ? selectedAssetId : (selectedAsset?.id || undefined),
      });

      addMessage(
        "assistant",
        response.response,
        response.intent,
        response.data
      );

      // Update nearby assets if returned
      if (response.data && response.data.type === "assets" && response.data.items) {
        setNearbyAssets(response.data.items);
      }
    } catch (e: any) {
      const detail = e?.response?.data?.detail || e?.message || "Unknown error";
      console.error("Chat API error:", detail, e);
      toast.error(`Error: ${detail}`);
    } finally {
      setIsTyping(false);
    }
  };

  const sendVoiceMessage = async (audioBlob: Blob) => {
    setIsTyping(true);
    try {
      addMessage("user", "[Voice Input]");
      const response = await chatApi.transcribeAudio(
        audioBlob,
        sessionId,
        location?.latitude || undefined,
        location?.longitude || undefined
      );

      addMessage(
        "assistant",
        response.response,
        response.intent,
        response.data
      );

      if (response.data && response.data.type === "assets" && response.data.items) {
        setNearbyAssets(response.data.items);
      }
      if (response.selected_asset_id && !selectedAsset) {
        const items = response.data?.items || [];
        const found = items.find((a: any) => a.id === response.selected_asset_id);
        if (found) setSelectedAssetState(found);
      }
    } catch (e) {
      toast.error("Failed to process voice command");
    } finally {
      setIsTyping(false);
    }
  };

  const identifyAssetFromFrame = async (imageBlob: Blob) => {
    setIsTyping(true);
    try {
      const recognized = await assetApi.identifyAsset(imageBlob);
      setSelectedAssetState(recognized);
      toast.success(`Identified: ${recognized.name} (${recognized.sku})`);

      // Let backend agent know that we scanned this asset
      await sendMessage(`I have physically scanned the asset: **${recognized.name}**.`);
    } catch (e) {
      toast.error("Failed to recognize asset");
    } finally {
      setIsTyping(false);
    }
  };

  const confirmCreateTicket = async () => {
    if (!currentTicketSummary) return;
    setIsTyping(true);
    try {
      const created = await ticketApi.createTicket({
        title: currentTicketSummary.title || "Reported Issue",
        description: currentTicketSummary.description || "No details provided",
        asset_id: currentTicketSummary.asset_id || 1,
        priority: currentTicketSummary.priority || "medium",
      });

      addMessage("assistant", `Ticket **#${created.id}** [${created.priority.toUpperCase()}] has been successfully created. I will notify the supervisor. Is there anything else you need help with?`);
      setCurrentTicketSummary(null);
    } catch (e) {
      toast.error("Failed to create ticket");
    } finally {
      setIsTyping(false);
    }
  };

  const resetChat = () => {
    setMessages([
      {
        id: "msg-init",
        role: "assistant",
        content: "Hello! I am your AI Assistant. Let's get started. May I access your browser location to locate nearby assets?",
        timestamp: new Date().toLocaleTimeString(),
      },
    ]);
    setSelectedAssetState(null);
    setNearbyAssets([]);
    setCurrentTicketSummary(null);
  };

  return (
    <ChatContext.Provider
      value={{
        messages,
        selectedAsset,
        location,
        locationStatus,
        nearbyAssets,
        currentTicketSummary,
        isTyping,
        sessionId,
        ttsEnabled,
        setTtsEnabled,
        sendMessage,
        sendVoiceMessage,
        identifyAssetFromFrame,
        setSelectedAsset,
        requestLocation,
        submitManualLocation,
        confirmCreateTicket,
        resetChat,
      }}
    >
      {children}
    </ChatContext.Provider>
  );
};

export const useChat = () => {
  const context = useContext(ChatContext);
  if (!context) throw new Error("useChat must be used within ChatProvider");
  return context;
};
