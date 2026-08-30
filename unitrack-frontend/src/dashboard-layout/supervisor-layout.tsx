/* eslint-disable @typescript-eslint/no-explicit-any */
import React, { useState } from "react";
import { Outlet } from "react-router-dom";
import { GraduationCap, Menu } from "lucide-react";
import Sidebar from "../components/sidebar";
import { useUserStore } from "../context/user-context";

const SupervisorDashboardLayout: React.FC = () => {
  const user = useUserStore((state) => state.user);
  const [sidebarOpen, setSidebarOpen] = useState(false);

  return (
    <div className="flex min-h-screen bg-gray-100">
      {/* Sidebar */}
      <Sidebar
        role={user?.role as any}
        isOpen={sidebarOpen}
        onClose={() => setSidebarOpen(false)}
      />

      {/* Main content */}
      <main className="flex-1 p-4 md:p-8 w-full min-h-screen">
        <header
          className="fixed top-0 left-0 w-full z-30 transition-all duration-500 
          bg-white/90 backdrop-blur-md shadow-md flex justify-between items-center
            "
        >
          <div className="flex items-center gap-3 py-4 px-4 md:px-6">
            {/* Mobile hamburger */}
            <button
              onClick={() => setSidebarOpen(true)}
              className="p-2 rounded-lg hover:bg-gray-100 md:hidden"
            >
              <Menu
                size={24}
                className="text-green-700"
              />
            </button>

            <a
              href="#"
              className="flex items-center gap-2"
            >
              <div className="w-9 h-9 rounded-full bg-green-600 flex items-center justify-center text-white font-bold">
                <GraduationCap />
              </div>
              <span className="text-xl font-semibold transition-colors duration-300 text-green-700">
                Unitrack
              </span>
            </a>
          </div>

          {/* profile */}
          <button className="rounded-full bg-green-700 text-white font-bold text-lg md:text-xl h-10 w-10 md:h-14 md:w-14 grid place-content-center mr-4 ">
            {user?.fullname
              ?.trim()
              .split(/\s+/)
              .map((w) => w[0] || "")
              .join("")
              .slice(0, 2)
              .toUpperCase() || ""}
          </button>
        </header>

        <Outlet />
      </main>
    </div>
  );
};

export default SupervisorDashboardLayout;
