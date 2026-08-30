import React from "react";
import { Link, useLocation } from "react-router-dom";
import {
  Home,
  Users,
  Folder,
  Settings,
  FilePlus,
  UserCheck,
  ClipboardList,
  X,
} from "lucide-react";

interface SidebarProps {
  role: "admin" | "supervisor" | "student" | null;
  isOpen: boolean;
  onClose: () => void;
}

const Sidebar: React.FC<SidebarProps> = ({ role, isOpen, onClose }) => {
  const location = useLocation();

  const menuItems = {
    admin: [
      { name: "Dashboard", path: "/admin-dashboard", icon: <Home size={20} /> },
      {
        name: "Assign Supervisors",
        path: "assign-supervisors",
        icon: <Users size={20} />,
      },
      {
        name: "All Projects",
        path: "/admin/projects",
        icon: <Folder size={20} />,
      },
      { name: "Settings", path: "/settings", icon: <Settings size={20} /> },
    ],

    supervisor: [
      {
        name: "Dashboard",
        path: "/supervisor-dashboard",
        icon: <Home size={20} />,
      },
      {
        name: "Assigned Students",
        path: "/supervisor/students",
        icon: <UserCheck size={20} />,
      },
      {
        name: "Project Reviews",
        path: "/supervisor/reviews",
        icon: <ClipboardList size={20} />,
      },
      { name: "Settings", path: "/settings", icon: <Settings size={20} /> },
    ],

    student: [
      {
        name: "Dashboard",
        path: "/student-dashboard",
        icon: <Home size={20} />,
      },
      {
        name: "My Project",
        path: "/student-dashboard/students/project",
        icon: <Folder size={20} />,
      },
      {
        name: "Upload Files",
        path: "/student/upload",
        icon: <FilePlus size={20} />,
      },
      { name: "Settings", path: "/settings", icon: <Settings size={20} /> },
    ],
  };

  const items = menuItems[role as keyof typeof menuItems] || [];

  return (
    <>
      {/* Mobile backdrop */}
      {isOpen && (
        <div
          className="fixed inset-0 bg-black/40 z-40 md:hidden"
          onClick={onClose}
        />
      )}

      {/* Sidebar */}
      <aside
        className={`
          fixed top-0 left-0 z-50 h-screen w-64 bg-green-700 text-white py-28 px-6
          transform transition-transform duration-300 ease-in-out
          md:relative md:translate-x-0 md:z-auto
          ${isOpen ? "translate-x-0" : "-translate-x-full"}
        `}
      >
        {/* Mobile close button */}
        <button
          onClick={onClose}
          className="absolute top-6 right-4 p-1 rounded-md hover:bg-green-600 md:hidden"
        >
          <X size={24} />
        </button>

        <nav className="space-y-2">
          {items.map((item) => {
            const isActive = location.pathname === item.path;

            return (
              <Link
                key={item.path}
                to={item.path}
                onClick={onClose}
                className={`flex items-center gap-3 px-4 py-2 rounded-md outline-none transition 
                ${
                  isActive
                    ? "bg-white text-green-700 font-semibold"
                    : "hover:bg-white hover:text-green-700"
                }
              `}
              >
                {item.icon}
                <span>{item.name}</span>
              </Link>
            );
          })}
        </nav>
      </aside>
    </>
  );
};

export default Sidebar;
