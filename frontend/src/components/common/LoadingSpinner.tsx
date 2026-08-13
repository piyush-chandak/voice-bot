import React from "react";
import { Loader2 } from "lucide-react";

export const LoadingSpinner: React.FC<{ size?: number; className?: string }> = ({
  size = 24,
  className = "",
}) => {
  return (
    <div className={`flex items-center justify-center p-4 ${className}`}>
      <Loader2 size={size} className="animate-spin text-primary" />
    </div>
  );
};
