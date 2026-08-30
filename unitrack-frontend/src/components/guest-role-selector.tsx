import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useUserStore } from "../context/user-context";
import { guestLogin } from "../lib/guest-auth";
import { User, Users, Briefcase } from "lucide-react";

interface GuestRoleSelectorProps {
  onClose: () => void;
}

const GuestRoleSelector: React.FC<GuestRoleSelectorProps> = ({ onClose }) => {
  const [selectedRole, setSelectedRole] = useState<
    "student" | "supervisor" | "admin" | null
  >(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const navigate = useNavigate();
  const setUser = useUserStore((state) => state.setUser);
  const setGuest = useUserStore((state) => state.setGuest);

  const roles = [
    {
      value: "student" as const,
      label: "Student",
      icon: User,
      description: "View student projects and assignments",
      color: "bg-blue-50 border-blue-200 hover:border-blue-400",
    },
    {
      value: "supervisor" as const,
      label: "Supervisor",
      icon: Briefcase,
      description: "View supervised students and projects",
      color: "bg-green-50 border-green-200 hover:border-green-400",
    },
    {
      value: "admin" as const,
      label: "Admin",
      icon: Users,
      description: "View dashboard and manage sessions",
      color: "bg-purple-50 border-purple-200 hover:border-purple-400",
    },
  ];

  const handleGuestLogin = async () => {
    if (!selectedRole) return;

    setLoading(true);
    setError("");

    try {
      const response = await guestLogin(selectedRole);

      // Normalize backend user to frontend `User` shape and ensure non-null
      const backendUser = response?.user ?? null;

      const backendTyped = backendUser as null | {
        id?: number;
        full_name?: string;
        email?: string;
        role?: string;
        staff_id?: string | null;
        matric_no?: string | null;
      };

      // Normalize role to the known guest roles so it matches the frontend User role type.
      const allowedRoles = ["student", "supervisor", "admin"] as const;
      type GuestRole = typeof allowedRoles[number];

      const normalizedRole: GuestRole =
        backendTyped && backendTyped.role && (allowedRoles as readonly string[]).includes(backendTyped.role)
          ? (backendTyped.role as GuestRole)
          : (selectedRole as GuestRole);

      const safeUser = {
        id: backendTyped?.id ?? 0,
        fullname: backendTyped?.full_name ?? `Guest ${selectedRole}`,
        email: backendTyped?.email ?? "",
        role: normalizedRole,
        staffId: backendTyped?.staff_id ?? undefined,
        matricNo: backendTyped?.matric_no ?? undefined,
      };

      setUser(safeUser);
      // set guest flag + role in store
      setGuest(true, selectedRole);

      // Redirect based on role
      const roleRoutes: Record<string, string> = {
        admin: "/admin-dashboard/",
        supervisor: "/supervisor-dashboard/",
        student: "/student-dashboard",
      };

      navigate(roleRoutes[selectedRole] || "/");
      // close the modal if provided
      onClose();
    } catch (err) {
      setError("Failed to login as guest. Please try again.");
      console.error("Guest login error:", err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div
      onClick={(e) => e.stopPropagation()}
      className="w-full md:w-[90%] max-w-2xl bg-white rounded-xl shadow-2xl p-8"
    >
      <h1 className="text-2xl font-bold text-gray-800 mb-2 text-center">
        Try as Guest
      </h1>
      <p className="text-gray-600 text-center mb-8">
        Select a role to explore the platform as a guest. (Read-only access)
      </p>

      {error && (
        <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg mb-6">
          {error}
        </div>
      )}

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-8">
        {roles.map((role) => {
          const Icon = role.icon;
          const isSelected = selectedRole === role.value;

          return (
            <button
              key={role.value}
              onClick={() => setSelectedRole(role.value)}
              className={`
                p-6 border-2 rounded-lg transition-all cursor-pointer
                ${
                  isSelected
                    ? role.color
                        .replace("hover:", "")
                        .replace("border", "border-2")
                    : role.color
                }
              `}
            >
              <Icon className="w-8 h-8 mx-auto mb-3 text-gray-700" />
              <h3 className="font-semibold text-gray-800 mb-1">{role.label}</h3>
              <p className="text-sm text-gray-600">{role.description}</p>
              {isSelected && (
                <div className="mt-3 flex justify-center">
                  <div className="w-2 h-2 bg-green-600 rounded-full"></div>
                </div>
              )}
            </button>
          );
        })}
      </div>

      <div className="flex gap-3">
        <button
          onClick={onClose}
          className="flex-1 bg-gray-200 hover:bg-gray-300 text-gray-800 font-semibold py-3 rounded-lg transition"
        >
          Cancel
        </button>
        <button
          onClick={handleGuestLogin}
          disabled={!selectedRole || loading}
          className={`
            flex-1 font-semibold py-3 rounded-lg transition
            ${
              selectedRole && !loading
                ? "bg-green-600 hover:bg-green-700 text-white cursor-pointer"
                : "bg-gray-300 text-gray-500 cursor-not-allowed"
            }
          `}
        >
          {loading ? "Logging in..." : "Continue as Guest"}
        </button>
      </div>
    </div>
  );
};

export default GuestRoleSelector;
