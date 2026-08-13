import React from "react";
import { useChat } from "../../contexts/ChatContext";
import { MapPin, Box, Wrench, AlertTriangle, Check, RefreshCw } from "lucide-react";

export const RightContextPanel: React.FC = () => {
  const {
    location,
    nearbyAssets,
    selectedAsset,
    setSelectedAsset,
    currentTicketSummary,
    confirmCreateTicket,
    locationStatus,
    requestLocation,
  } = useChat();

  return (
    <aside className="w-80 border-l border-border/80 bg-card overflow-y-auto p-5 hidden xl:flex flex-col gap-6">
      {/* 1. Location Status widget */}
      <div className="bg-secondary/50 rounded-2xl p-4 border border-border/50">
        <h3 className="text-sm font-semibold flex items-center gap-2 mb-3">
          <MapPin size={16} className="text-primary" />
          Location Telemetry
        </h3>
        {location ? (
          <div className="text-xs space-y-1 text-muted-foreground font-mono">
            <p>Latitude: {location.latitude.toFixed(6)}</p>
            <p>Longitude: {location.longitude.toFixed(6)}</p>
          </div>
        ) : (
          <div className="space-y-3">
            <p className="text-xs text-muted-foreground">
              Request browser location to locate assets.
            </p>
            <button
              onClick={requestLocation}
              disabled={locationStatus === "requesting"}
              className="w-full text-xs font-semibold py-2 bg-primary text-white rounded-xl shadow-md shadow-primary/10 hover:bg-primary/95 transition-all flex items-center justify-center gap-2"
            >
              {locationStatus === "requesting" && <RefreshCw size={12} className="animate-spin" />}
              Request Geolocation
            </button>
          </div>
        )}
      </div>

      {/* 2. Selected Asset details */}
      {selectedAsset && (
        <div className="bg-primary/5 rounded-2xl p-4 border border-primary/10">
          <h3 className="text-sm font-semibold flex items-center gap-2 mb-3 text-primary">
            <Box size={16} />
            Selected Asset
          </h3>
          <div className="text-sm">
            <h4 className="font-semibold text-foreground">{selectedAsset.name}</h4>
            <p className="text-xs font-mono text-muted-foreground mt-0.5">{selectedAsset.sku}</p>
            <p className="text-xs text-muted-foreground mt-2">{selectedAsset.description}</p>
            <div className="mt-3 flex items-center gap-2">
              <span
                className={`w-2.5 h-2.5 rounded-full ${selectedAsset.status === "operational" ? "bg-emerald-500" : "bg-amber-500"
                  }`}
              />
              <span className="text-xs font-semibold capitalize text-foreground">
                {selectedAsset.status?.replace("_", " ")}
              </span>
            </div>
          </div>
        </div>
      )}

      {/* 3. Ticket Summary Draft (Prompting confirmation) */}
      {currentTicketSummary && (
        <div className="bg-destructive/5 rounded-2xl p-4 border border-destructive/15 shadow-sm">
          <h3 className="text-sm font-bold flex items-center gap-2 mb-3 text-destructive">
            <AlertTriangle size={16} />
            Draft Ticket Summary
          </h3>
          <div className="space-y-3 text-sm">
            <div>
              <span className="text-xs text-muted-foreground font-semibold">Title</span>
              <p className="font-medium text-foreground">{currentTicketSummary.title}</p>
            </div>
            <div>
              <span className="text-xs text-muted-foreground font-semibold">Description</span>
              <p className="text-xs text-muted-foreground line-clamp-3">
                {currentTicketSummary.description}
              </p>
            </div>
            <div className="flex gap-4">
              <div>
                <span className="text-xs text-muted-foreground font-semibold">Priority</span>
                <span className="block text-xs font-bold text-destructive uppercase">
                  {currentTicketSummary.priority}
                </span>
              </div>
              <div>
                <span className="text-xs text-muted-foreground font-semibold">Asset ID</span>
                <span className="block text-xs font-mono">{currentTicketSummary.asset_id}</span>
              </div>
            </div>
            <button
              onClick={confirmCreateTicket}
              className="w-full py-2 bg-emerald-500 text-white font-bold rounded-xl shadow-md shadow-emerald-500/10 hover:bg-emerald-600 transition-all flex items-center justify-center gap-2"
            >
              <Check size={16} />
              Create Work Ticket
            </button>
          </div>
        </div>
      )}

      {/* 4. Nearby Assets list */}
      {nearbyAssets.length > 0 && (
        <div className="flex-1 flex flex-col min-h-0">
          <h3 className="text-sm font-semibold flex items-center gap-2 mb-3 shrink-0">
            <Wrench size={16} className="text-primary" />
            Assets in Range (50m)
          </h3>
          <div className="flex-1 overflow-y-auto space-y-3 pr-1">
            {nearbyAssets.map((asset) => {
              const isSelected = selectedAsset?.id === asset.id;
              return (
                <div
                  key={asset.id}
                  onClick={() => setSelectedAsset(asset)}
                  className={`p-3.5 rounded-xl border text-left cursor-pointer transition-all ${isSelected
                    ? "border-primary bg-primary/5 ring-1 ring-primary"
                    : "border-border hover:border-muted-foreground/30 bg-card"
                    }`}
                >
                  <h4 className="font-semibold text-sm text-foreground line-clamp-1">
                    {asset.name}
                  </h4>
                  <p className="text-xs font-mono text-muted-foreground mt-0.5">{asset.sku}</p>
                  <div className="mt-2 flex items-center justify-between text-[11px] text-muted-foreground">
                    <span>Dist: {asset.distance || 15}m</span>
                    <span
                      className={`px-2 py-0.5 rounded-full font-bold uppercase ${asset.status === "operational"
                        ? "bg-emerald-500/10 text-emerald-600"
                        : "bg-amber-500/10 text-amber-600"
                        }`}
                    >
                      {asset.status?.replace("_", " ")}
                    </span>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}
    </aside>
  );
};
