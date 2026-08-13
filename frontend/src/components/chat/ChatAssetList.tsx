import React from "react";
import { useNavigate } from "react-router-dom";
import { Asset } from "../../types";
import { CheckCircle, ExternalLink } from "lucide-react";

interface ChatAssetListProps {
  assets: Asset[];
  selectedAsset: Asset | null;
  onSelectAsset: (asset: Asset) => void;
}

export const ChatAssetList: React.FC<ChatAssetListProps> = ({
  assets,
  selectedAsset,
  onSelectAsset,
}) => {
  const navigate = useNavigate();

  return (
    <div className="pl-12 pr-4 flex flex-wrap gap-3">
      {assets.map((asset) => {
        const isSelected = selectedAsset?.id === asset.id;
        return (
          <div
            key={asset.id}
            className={`p-4 rounded-2xl border text-left transition-all w-64 max-w-full flex flex-col justify-between ${
              isSelected
                ? "border-primary bg-primary/5 ring-1 ring-primary"
                : "border-border hover:border-muted-foreground/30 bg-card"
            }`}
          >
            <div>
              <h4 className="font-bold text-sm text-foreground line-clamp-1">
                {asset.name}
              </h4>
              <p className="text-[10px] font-mono text-muted-foreground mt-0.5">
                {asset.sku}
              </p>
              <p className="text-xs text-muted-foreground mt-2 line-clamp-2">
                {asset.description}
              </p>
            </div>

            <div className="mt-4 space-y-2">
              <button
                onClick={() => onSelectAsset(asset)}
                className={`w-full py-2 rounded-xl text-xs font-bold transition-all flex items-center justify-center gap-1.5 ${
                  isSelected
                    ? "bg-emerald-500 text-white hover:bg-emerald-600"
                    : "bg-secondary text-foreground hover:bg-secondary/80 border border-border/80"
                }`}
              >
                {isSelected ? (
                  <>
                    <CheckCircle size={12} />
                    Selected
                  </>
                ) : (
                  "Select Asset"
                )}
              </button>

              <button
                onClick={() => navigate(`/assets?id=${asset.id}`)}
                className="w-full py-1.5 rounded-xl text-xs font-semibold text-primary hover:bg-primary/10 border border-primary/20 transition-all flex items-center justify-center gap-1"
              >
                <ExternalLink size={12} />
                View Asset Details
              </button>
            </div>
          </div>
        );
      })}
    </div>
  );
};
