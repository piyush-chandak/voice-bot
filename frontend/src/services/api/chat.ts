import { apiClient, isOfflineMock } from "./client";

interface ChatPayload {
  message: string;
  session_id: string;
  latitude?: number;
  longitude?: number;
  selected_asset_id?: number;
}

interface ChatResponse {
  response: string;
  session_id: string;
  latitude?: number;
  longitude?: number;
  selected_asset_id?: number;
  active_ticket_id?: number;
  active_asset_id?: number;
  nearby_assets?: any[];
  intent?: string;
  data?: any;
}


export const chatApi = {
  sendChatMessage: async (payload: ChatPayload): Promise<ChatResponse> => {
    // if (isOfflineMock) {
    //   // Simulate network delay
    //   await new Promise((resolve) => setTimeout(resolve, 800));

    //   const msg = payload.message.toLowerCase();
    //   let response = "I'm processing your request. How can I assist you with the selected asset?";
    //   let nearby_assets: any[] | undefined = undefined;
    //   let selected_asset_id: number | undefined = undefined;

    //   if (msg.includes("location") || msg.includes("nearby") || msg.includes("greet")) {
    //     response = "Checking your location... I found 2 assets within 50 meters. Main Water Pump A and Electrical Transformer Grid-3.";
    //     nearby_assets = [
    //       {
    //         id: 1,
    //         name: "Main Water Pump A",
    //         description: "Primary water distribution valve and flow rate pump.",
    //         sku: "PUMP-WTR-001",
    //         latitude: 37.7749,
    //         longitude: -122.4194,
    //         status: "operational",
    //       },
    //       {
    //         id: 2,
    //         name: "Electrical Transformer Grid-3",
    //         description: "High voltage power grid distribution block.",
    //         sku: "ELEC-TRN-003",
    //         latitude: 37.7750,
    //         longitude: -122.4193,
    //         status: "maintenance_required",
    //       },
    //     ];
    //   } else if (msg.includes("leak") || msg.includes("broken")) {
    //     response = "I have summarized the issue. Leak detected on Main Water Pump A. Ready to create a high-priority ticket. Please click Confirm in the ticket summary widget.";
    //   }

    //   return {
    //     response,
    //     session_id: payload.session_id,
    //     latitude: payload.latitude || 37.7749,
    //     longitude: payload.longitude || -122.4194,
    //     nearby_assets,
    //     selected_asset_id,
    //   };
    // }

    const response = await apiClient.post<ChatResponse>("/chat", payload);
    return response.data;
  },

  transcribeAudio: async (
    audioBlob: Blob,
    sessionId: string,
    latitude?: number,
    longitude?: number
  ): Promise<ChatResponse> => {
    if (isOfflineMock) {
      await new Promise((resolve) => setTimeout(resolve, 1500));
      return {
        response: "I transcribed your voice recording. Here is the response: Nearby assets have been loaded.",
        session_id: sessionId,
        latitude: latitude || 37.7749,
        longitude: longitude || -122.4194,
        nearby_assets: [
          {
            id: 1,
            name: "Main Water Pump A",
            description: "Primary water distribution valve and flow rate pump.",
            sku: "PUMP-WTR-001",
            latitude: 37.7749,
            longitude: -122.4194,
            status: "operational",
          }
        ],
      };
    }
    const formData = new FormData();
    formData.append("file", audioBlob, "voice.wav");
    formData.append("session_id", sessionId);
    if (latitude !== undefined) {
      formData.append("latitude", latitude.toString());
    }
    if (longitude !== undefined) {
      formData.append("longitude", longitude.toString());
    }

    const response = await apiClient.post<ChatResponse>("/voice", formData, {
      headers: {
        "Content-Type": "multipart/form-data",
      },
    });
    return response.data;
  },

  getLivekitToken: async (
    roomName: string,
    sessionId?: string,
    latitude?: number,
    longitude?: number
  ): Promise<{ token: string; url: string; room_name: string }> => {
    const response = await apiClient.post<{ token: string; url: string; room_name: string }>("/voice/token", {
      room_name: roomName,
      session_id: sessionId,
      latitude: latitude,
      longitude: longitude,
    });
    return response.data;
  },

  getVoiceSessionState: async (sessionId: string): Promise<any> => {
    const response = await apiClient.get<any>("/voice/state", {
      params: { session_id: sessionId },
    });
    return response.data;
  },
};
