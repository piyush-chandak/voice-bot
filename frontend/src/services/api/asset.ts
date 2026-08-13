import { apiClient } from "./client";
import { Asset } from "../../types";

export const assetApi = {
  getAssets: async (): Promise<Asset[]> => {
    const response = await apiClient.get<Asset[]>("/assets");
    return response.data;
  },

  getNearbyAssets: async (latitude: number, longitude: number, radius = 50.0): Promise<Asset[]> => {
    const response = await apiClient.get<Asset[]>("/assets/nearby", {
      params: { latitude, longitude, radius_meters: radius },
    });
    return response.data;
  },

  createAsset: async (asset: Omit<Asset, "id">): Promise<Asset> => {
    const response = await apiClient.post<Asset>("/assets", asset);
    return response.data;
  },

  updateAsset: async (id: number, asset: Partial<Omit<Asset, "id">>): Promise<Asset> => {
    const response = await apiClient.put<Asset>(`/assets/${id}`, asset);
    return response.data;
  },

  deleteAsset: async (id: number): Promise<Asset> => {
    const response = await apiClient.delete<Asset>(`/assets/${id}`);
    return response.data;
  },

  identifyAsset: async (file: Blob | File): Promise<Asset> => {
    const formData = new FormData();
    formData.append("file", file, "frame.jpg");
    const response = await apiClient.post<Asset>("/assets/identify", formData, {
      headers: {
        "Content-Type": "multipart/form-data",
      },
    });
    return response.data;
  },
};
