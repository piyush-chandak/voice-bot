import React, { useState, useEffect } from "react";
import { useSearchParams } from "react-router-dom";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { assetApi } from "../services/api/asset";
import { Search, MapPin, ShieldCheck, Plus, Pencil, Trash2, X } from "lucide-react";
import { Asset } from "../types";
import toast from "react-hot-toast";

export const Assets: React.FC = () => {
  const [searchParams] = useSearchParams();
  const targetId = searchParams.get("id");
  const [searchTerm, setSearchTerm] = useState("");
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [editingAsset, setEditingAsset] = useState<Asset | null>(null);

  // Form states
  const [name, setName] = useState("");
  const [sku, setSku] = useState("");
  const [description, setDescription] = useState("");
  const [latitude, setLatitude] = useState("");
  const [longitude, setLongitude] = useState("");
  const [status, setStatus] = useState("operational");

  const queryClient = useQueryClient();

  const { data: assets = [], isLoading } = useQuery({
    queryKey: ["assets"],
    queryFn: () => assetApi.getAssets(),
  });

  useEffect(() => {
    if (targetId && assets.length > 0) {
      const found = assets.find((a) => a.id === parseInt(targetId, 10));
      if (found) {
        setSearchTerm(found.name);
        openEditModal(found);
      }
    }
  }, [targetId, assets]);


  const createMutation = useMutation({
    mutationFn: (newAsset: Omit<Asset, "id">) => assetApi.createAsset(newAsset),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["assets"] });
      toast.success("Asset created successfully");
      closeModal();
    },
    onError: (err: any) => {
      toast.error(err.response?.data?.detail || "Failed to create asset");
    },
  });

  const updateMutation = useMutation({
    mutationFn: ({ id, asset }: { id: number; asset: Partial<Omit<Asset, "id">> }) =>
      assetApi.updateAsset(id, asset),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["assets"] });
      toast.success("Asset updated successfully");
      closeModal();
    },
    onError: (err: any) => {
      toast.error(err.response?.data?.detail || "Failed to update asset");
    },
  });

  const deleteMutation = useMutation({
    mutationFn: (id: number) => assetApi.deleteAsset(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["assets"] });
      toast.success("Asset deleted successfully");
    },
    onError: (err: any) => {
      toast.error(err.response?.data?.detail || "Failed to delete asset");
    },
  });

  const openAddModal = () => {
    setEditingAsset(null);
    setName("");
    setSku("");
    setDescription("");
    setLatitude("");
    setLongitude("");
    setStatus("operational");
    setIsModalOpen(true);
  };

  const openEditModal = (asset: Asset) => {
    setEditingAsset(asset);
    setName(asset.name);
    setSku(asset.sku);
    setDescription(asset.description || "");
    setLatitude(asset.latitude.toString());
    setLongitude(asset.longitude.toString());
    setStatus(asset.status);
    setIsModalOpen(true);
  };

  const closeModal = () => {
    setIsModalOpen(false);
    setEditingAsset(null);
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!name || !sku || !latitude || !longitude) {
      toast.error("Please fill in all required fields");
      return;
    }

    const latVal = parseFloat(latitude);
    const lonVal = parseFloat(longitude);

    if (isNaN(latVal) || latVal < -90 || latVal > 90) {
      toast.error("Latitude must be a number between -90 and 90");
      return;
    }
    if (isNaN(lonVal) || lonVal < -180 || lonVal > 180) {
      toast.error("Longitude must be a number between -180 and 180");
      return;
    }

    const payload = {
      name,
      sku,
      description: description || undefined,
      latitude: latVal,
      longitude: lonVal,
      status,
    };

    if (editingAsset) {
      updateMutation.mutate({ id: editingAsset.id, asset: payload });
    } else {
      createMutation.mutate(payload);
    }
  };

  const handleDelete = (id: number) => {
    if (window.confirm("Are you sure you want to delete this asset?")) {
      deleteMutation.mutate(id);
    }
  };

  const filteredAssets = assets.filter(
    (asset) =>
      asset.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      asset.sku.toLowerCase().includes(searchTerm.toLowerCase())
  );

  return (
    <div className="p-6 space-y-6 flex-1 flex flex-col min-h-0">
      {/* Header */}
      <div className="flex items-center justify-between shrink-0">
        <div>
          <h1 className="text-2xl font-bold text-foreground">Assets Catalog</h1>
          <p className="text-sm text-muted-foreground mt-0.5">
            Audit catalog profiles, look up coordinates, or search details.
          </p>
        </div>
        <button
          onClick={openAddModal}
          className="flex items-center gap-2 px-4 py-2.5 bg-primary hover:bg-primary/95 text-white font-bold text-sm rounded-xl transition-all shadow-md shadow-primary/25"
        >
          <Plus size={16} />
          Add Asset
        </button>
      </div>

      {/* Filter Row */}
      <div className="flex shrink-0 bg-card p-4 rounded-2xl border border-border/80 shadow-sm">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-2.5 text-muted-foreground" size={16} />
          <input
            type="text"
            placeholder="Search assets by name or SKU..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-full h-10 pl-10 pr-4 bg-secondary/80 border border-border/60 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-primary/20 text-foreground"
          />
        </div>
      </div>

      {/* Grid List */}
      <div className="flex-1 overflow-y-auto min-h-0">
        {isLoading ? (
          <div className="text-center text-sm text-muted-foreground p-8">Loading assets...</div>
        ) : filteredAssets.length === 0 ? (
          <div className="text-center text-sm text-muted-foreground p-8">No assets matching search.</div>
        ) : (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6 pb-6">
            {filteredAssets.map((asset) => (
              <div
                key={asset.id}
                className="bg-card border border-border/80 rounded-2xl p-5 shadow-sm hover:shadow-md transition-all flex flex-col justify-between"
              >
                <div>
                  <div className="flex items-center justify-between mb-3">
                    <span className="text-[10px] text-muted-foreground font-mono font-bold uppercase">
                      ID #{asset.id}
                    </span>
                    <div className="flex items-center gap-2">
                      <span
                        className={`px-2 py-0.5 rounded-full text-xs font-bold uppercase ${asset.status === "operational"
                            ? "bg-emerald-500/10 text-emerald-600"
                            : "bg-amber-500/10 text-amber-600"
                          }`}
                      >
                        {asset.status?.replace("_", " ")}
                      </span>
                    </div>
                  </div>

                  <h3 className="font-bold text-foreground text-base mb-1">{asset.name}</h3>
                  <span className="text-xs text-muted-foreground font-mono font-medium block">
                    {asset.sku}
                  </span>
                  <p className="text-xs text-muted-foreground mt-3 leading-relaxed">
                    {asset.description || "No description provided."}
                  </p>
                </div>

                <div className="border-t border-border/50 pt-4 mt-5">
                  <div className="flex items-center justify-between text-xs text-muted-foreground mb-4">
                    <div className="flex items-center gap-1">
                      <MapPin size={14} className="text-primary" />
                      <span>
                        {asset.latitude.toFixed(4)}, {asset.longitude.toFixed(4)}
                      </span>
                    </div>
                    <div className="flex items-center gap-1 font-semibold">
                      <ShieldCheck size={14} className="text-emerald-500" />
                      <span>Certified</span>
                    </div>
                  </div>

                  {/* Actions */}
                  <div className="flex gap-2 justify-end border-t border-border/30 pt-3">
                    <button
                      onClick={() => openEditModal(asset)}
                      className="p-2 hover:bg-secondary text-muted-foreground hover:text-foreground rounded-lg transition-colors border border-border/60"
                      title="Edit Asset"
                    >
                      <Pencil size={14} />
                    </button>
                    <button
                      onClick={() => handleDelete(asset.id)}
                      className="p-2 hover:bg-destructive/10 text-muted-foreground hover:text-destructive rounded-lg transition-colors border border-border/60"
                      title="Delete Asset"
                    >
                      <Trash2 size={14} />
                    </button>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Form Modal */}
      {isModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm">
          <div className="w-full max-w-lg bg-card border border-border/80 rounded-2xl shadow-xl overflow-hidden flex flex-col max-h-[90vh]">
            {/* Modal Header */}
            <div className="flex items-center justify-between p-5 border-b border-border/80">
              <h2 className="text-lg font-bold text-foreground">
                {editingAsset ? "Edit Asset" : "Add Asset"}
              </h2>
              <button
                onClick={closeModal}
                className="p-1 hover:bg-secondary rounded-lg text-muted-foreground hover:text-foreground transition-colors"
              >
                <X size={18} />
              </button>
            </div>

            {/* Modal Form */}
            <form onSubmit={handleSubmit} className="p-5 space-y-4 overflow-y-auto">
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-1">
                  <label className="text-xs font-semibold text-muted-foreground uppercase tracking-wider">
                    Asset Name *
                  </label>
                  <input
                    type="text"
                    required
                    value={name}
                    onChange={(e) => setName(e.target.value)}
                    placeholder="Main Water Pump A"
                    className="w-full h-10 px-3 bg-secondary/80 border border-border rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-primary/20 text-foreground"
                  />
                </div>
                <div className="space-y-1">
                  <label className="text-xs font-semibold text-muted-foreground uppercase tracking-wider">
                    SKU Code *
                  </label>
                  <input
                    type="text"
                    required
                    value={sku}
                    onChange={(e) => setSku(e.target.value)}
                    placeholder="PUMP-WTR-001"
                    className="w-full h-10 px-3 bg-secondary/80 border border-border rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-primary/20 text-foreground"
                  />
                </div>
              </div>

              <div className="space-y-1">
                <label className="text-xs font-semibold text-muted-foreground uppercase tracking-wider">
                  Description
                </label>
                <textarea
                  value={description}
                  onChange={(e) => setDescription(e.target.value)}
                  placeholder="Primary water distribution valve and flow rate pump..."
                  rows={3}
                  className="w-full p-3 bg-secondary/80 border border-border rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-primary/20 text-foreground resize-none"
                />
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-1">
                  <label className="text-xs font-semibold text-muted-foreground uppercase tracking-wider">
                    Latitude *
                  </label>
                  <input
                    type="text"
                    required
                    value={latitude}
                    onChange={(e) => setLatitude(e.target.value)}
                    placeholder="37.7749"
                    className="w-full h-10 px-3 bg-secondary/80 border border-border rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-primary/20 text-foreground"
                  />
                </div>
                <div className="space-y-1">
                  <label className="text-xs font-semibold text-muted-foreground uppercase tracking-wider">
                    Longitude *
                  </label>
                  <input
                    type="text"
                    required
                    value={longitude}
                    onChange={(e) => setLongitude(e.target.value)}
                    placeholder="-122.4194"
                    className="w-full h-10 px-3 bg-secondary/80 border border-border rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-primary/20 text-foreground"
                  />
                </div>
              </div>

              <div className="space-y-1">
                <label className="text-xs font-semibold text-muted-foreground uppercase tracking-wider">
                  Status
                </label>
                <select
                  value={status}
                  onChange={(e) => setStatus(e.target.value)}
                  className="w-full h-10 px-3 bg-secondary/80 border border-border rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-primary/20 text-foreground"
                >
                  <option value="operational">Operational</option>
                  <option value="maintenance_required">Maintenance Required</option>
                  <option value="down">Down</option>
                </select>
              </div>

              {/* Modal Actions */}
              <div className="flex gap-3 justify-end pt-4 border-t border-border/80">
                <button
                  type="button"
                  onClick={closeModal}
                  className="px-4 py-2 border border-border text-sm font-semibold rounded-xl hover:bg-secondary transition-colors"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={createMutation.isPending || updateMutation.isPending}
                  className="px-4 py-2 bg-primary hover:bg-primary/95 text-white font-bold text-sm rounded-xl transition-all shadow-md shadow-primary/20"
                >
                  {editingAsset ? "Save Changes" : "Create Asset"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
