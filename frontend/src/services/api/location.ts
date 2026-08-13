import { apiClient, isOfflineMock } from "./client";

interface LocationPayload {
  latitude: number;
  longitude: number;
  accuracy?: number;
}

export const locationApi = {
  saveLocation: async (payload: LocationPayload): Promise<{ success: boolean }> => {
    if (isOfflineMock) {
      return { success: true };
    }
    await apiClient.post("/location", payload);
    return { success: true };
  },
};
