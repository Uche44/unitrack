import Overview from "../../../components/overview";
import PendingSupervisorsList from "../../../components/supervisor-list";
import ApprovedSupervisorsList from "../../../components/approved-supervisors";
import AssignedStudentsList from "../../../components/assigned-students";
import { Users, GraduationCap, FolderKanban } from "lucide-react";
import { useState } from "react";
import CreateSession from "../../../components/set-session";
import { useSessionStore } from "../../../context/session-context";
import GuestBanner from "../../../components/guest-banner";
import { useGuestMode } from "../../../hooks/useGuestMode";

const Admin: React.FC = () => {
  const [showSessionModal, setShowSessionModal] = useState<boolean>(false);
  const currentSession = useSessionStore((state) => state.currentSession);
  const { isGuest } = useGuestMode();

  const overviewData = [
    {
      label: "Supervisors",
      value: 230,
      icon: Users,
      bg: "bg-blue-100 dark:bg-blue-900",
      circleBg: "bg-blue-200 dark:bg-blue-800",
    },
    {
      label: "Students",
      value: 2300,
      icon: GraduationCap,
      bg: "bg-green-100 dark:bg-green-900",
      circleBg: "bg-green-200 dark:bg-green-800",
    },
    {
      label: "Projects",
      value: 2300,
      icon: FolderKanban,
      bg: "bg-yellow-100 dark:bg-yellow-900",
      circleBg: "bg-yellow-200 dark:bg-yellow-800",
    },
  ];

  return (
    <section className=" p-1  w-full min-h-screen">
      <GuestBanner />
      <div className="w-full mt-9 p-4 flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
        <h1 className="text-2xl md:text-3xl font-bold text-green-700">
          Welcome Admin!
        </h1>
        {currentSession ? (
          <div className="bg-green-50 border-2 border-green-400 rounded-xl p-4 max-w-md">
            {/* <p className="text-sm font-semibold text-green-700 mb-2">
              Current Session
            </p> */}
            <div className="space-y-1 text-sm text-green-700">
              <p>
                <span className="font-semibold"> Current Session:</span>{" "}
                {currentSession.session}
              </p>
              {/* <p>
                <span className="font-semibold">Duration:</span>{" "}
                {currentSession.duration}
              </p> */}
              {/* <p>
                <span className="font-semibold">Start:</span>{" "}
                {new Date(currentSession.start_date).toLocaleDateString()}
              </p> */}
              {/* <p>
                <span className="font-semibold">End:</span>{" "}
                {new Date(currentSession.end_date).toLocaleDateString()}
              </p> */}
            </div>
          </div>
        ) : (
          <button
            onClick={() => setShowSessionModal(true)}
            disabled={isGuest}
            className={`md:h-12 cursor-pointer text-white px-3 rounded-xl transition ${
              isGuest
                ? "bg-gray-400 cursor-not-allowed"
                : "bg-red-600 hover:brightness-105"
            }`}
          >
            Set Session
          </button>
        )}
      </div>

      {showSessionModal && (
        <div
          className="fixed inset-0 bg-black/20 flex items-center justify-center z-50 overflow-y-auto p-4"
          onClick={() => setShowSessionModal(false)} // CLICK OUTSIDE CLOSES
        >
          {/* <div
            className="max-h-[90vh] overflow-y-auto"
            onClick={(e) => e.stopPropagation()} // PREVENT INNER CLICK FROM CLOSING
          > */}
          <CreateSession closeModal={() => setShowSessionModal(false)} />
          {/* </div> */}
        </div>
      )}

      <Overview data={overviewData} />
      <PendingSupervisorsList />
      <ApprovedSupervisorsList />
      <AssignedStudentsList />
    </section>
  );
};

export default Admin;
