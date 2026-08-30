import React from "react";
import { AlertCircle, LogOut } from "lucide-react";
import { useUserStore } from "../context/user-context";
import { useNavigate } from "react-router-dom";

const GuestBanner: React.FC = () => {
  const is_guest = useUserStore((state) => state.is_guest);
  const guest_role = useUserStore((state) => state.guest_role);
  const clearUser = useUserStore((state) => state.clearUser);
  const navigate = useNavigate();

  if (!is_guest) return null;

  const handleLogout = () => {
    clearUser();
    navigate("/auth/login");
  };

  return (
    <div className="bg-yellow-50 mt-12 border-l-4 border-yellow-400 p-4 mb-6">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <AlertCircle className="text-yellow-600 w-5 h-5" />
          <div>
            <p className="font-semibold text-yellow-800">
              Guest Mode - Read Only
            </p>
            <p className="text-sm text-yellow-700">
              You are viewing as a guest {guest_role && `(${guest_role})`}. Edit
              features are disabled.
            </p>
          </div>
        </div>
        <button
          onClick={handleLogout}
          className="flex items-center gap-2 bg-yellow-600 hover:bg-yellow-700 text-white px-4 py-2 rounded-lg transition"
        >
          <LogOut className="w-4 h-4" />
          Exit Guest Mode
        </button>
      </div>
    </div>
  );
};

export default GuestBanner;
