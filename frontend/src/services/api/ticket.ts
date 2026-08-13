import { apiClient } from "./client";
import { Ticket } from "../../types";

export const ticketApi = {
  getTickets: async (myTicketsOnly = false): Promise<Ticket[]> => {
    const params: any = { my_tickets_only: myTicketsOnly };
    const cached = localStorage.getItem("technician_location");
    if (cached) {
      try {
        const { latitude, longitude } = JSON.parse(cached);
        params.latitude = latitude;
        params.longitude = longitude;
        params.radius_meters = 500.0;
      } catch (e) {
        console.error("Failed to parse cached location in getTickets", e);
      }
    }
    const response = await apiClient.get<Ticket[]>("/tickets", {
      params,
    });
    return response.data;
  },

  createTicket: async (payload: {
    title: string;
    description: string;
    asset_id: number;
    priority: string;
  }): Promise<Ticket> => {
    const response = await apiClient.post<Ticket>("/tickets", payload);
    return response.data;
  },

  updateTicket: async (id: number, payload: Partial<Ticket>): Promise<Ticket> => {
    const response = await apiClient.patch<Ticket>(`/tickets/${id}`, payload);
    return response.data;
  },
};
