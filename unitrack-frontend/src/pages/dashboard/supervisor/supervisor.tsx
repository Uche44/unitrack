import { useUserStore } from "../../../context/user-context";
import Overview from "../../../components/overview";
import { FolderCheck, GraduationCap, FolderKanban } from "lucide-react";
import StudentsUnderSupervision from "../../../components/students-under-supervision";
// import GuestBanner from "../../../components/guest-banner";

const Supervisor: React.FC = () => {
  const user = useUserStore((state) => state.user);
  console.log(user);
  const supervisorOverviewData = [
    {
      label: "Assigned Students",
      value: 5,
      icon: GraduationCap,
      bg: "bg-green-100 dark:bg-green-900",
      circleBg: "bg-green-200 dark:bg-green-800",
    },
    {
      label: "Projects",
      value: 0,
      icon: FolderKanban,
      bg: "bg-yellow-100 dark:bg-yellow-900",
      circleBg: "bg-yellow-200 dark:bg-yellow-800",
    },
    {
      label: "Projects Completed",
      value: 0,
      icon: FolderCheck,
      bg: "bg-blue-100 dark:bg-blue-900",
      circleBg: "bg-blue-200 dark:bg-blue-800",
    },
  ];

  return (
    <section className="w-full min-h-screen">
      {/* <GuestBanner /> */}
      <h1 className="mt-12 text-3xl font-bold text-green-700">
        Welcome Sp. {user?.fullname}!
      </h1>
      <Overview data={supervisorOverviewData} />
      <StudentsUnderSupervision supervisorId={user?.id} />
    </section>
  );
};

export default Supervisor;
