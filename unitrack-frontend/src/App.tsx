import React from "react";
import { createBrowserRouter, RouterProvider } from "react-router-dom";
import Home from "./pages/home";
import StudentForm from "./pages/studentform";
import SupervisorForm from "./pages/supervisorform";
import LoginForm from "./pages/login";
import AdminDashboardLayout from "./dashboard-layout/admin-layout";
import Admin from "./pages/dashboard/admin/admin";
import Students from "./pages/dashboard/student/students";
import Supervisor from "./pages/dashboard/supervisor/supervisor";
import SupervisorDashboardLayout from "./dashboard-layout/supervisor-layout";
import AssignSupervisor from "./pages/dashboard/admin/assign-supervisor";
import StudentPage from "./pages/dashboard/supervisor/student-page";
import StudentDashboardLayout from "./dashboard-layout/student-layout";
// import ProjectDash from "./pages/dashboard/student/projects";
import ProjectDashboard from "./pages/dashboard/student/projects";
import ProfilePage from "./pages/dashboard/profile";
import { Toaster } from "react-hot-toast";
import RequireRole from "./components/require-role";

// import NotFound from "./components/NotFound";
// import { Toaster } from "./components/ui/sonner";

const router = createBrowserRouter([
  {
    path: "/",
    element: <Home />,
  },

  {
    path: "/auth/students",
    element: <StudentForm />,
  },
  {
    path: "/auth/supervisors",
    element: <SupervisorForm />,
  },
  {
    path: "/auth/login",
    element: <LoginForm />,
  },

  {
    path: "/admin-dashboard",
    element: (
      <RequireRole role="admin">
        <AdminDashboardLayout />
      </RequireRole>
    ),
    children: [
      {
        index: true,
        element: <Admin />,
      },
      {
        path: "assign-supervisors",
        element: <AssignSupervisor />,
      },
    ],
  },

  {
    path: "/supervisor-dashboard",
    element: (
      <RequireRole role="supervisor">
        <SupervisorDashboardLayout />
      </RequireRole>
    ),
    children: [
      {
        index: true,
        element: <Supervisor />,
      },
      {
        path: "supervisors/:supervisorId/students/:studentId",
        element: <StudentPage />,
      },
      {
        path: "profile",
        element: <ProfilePage />,
      },
    ],
  },

  {
    path: "/student-dashboard",
    element: (
      <RequireRole role="student">
        <StudentDashboardLayout />
      </RequireRole>
    ),
    children: [
      {
        index: true,
        element: <Students />,
      },
      {
        path: "students/project/",
        element: <ProjectDashboard />,
      },
      {
        path: "profile",
        element: <ProfilePage />,
      },
      // {
      //   path: "assign-supervisors",
      //   element: <AssignSupervisor />,
      // },
    ],
  },
]);

const App: React.FC = () => {
  return (
    <>
      <Toaster position="top-right" />
      <RouterProvider router={router} />
    </>
  );
};

export default App;
