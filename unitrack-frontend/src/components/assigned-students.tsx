/* eslint-disable @typescript-eslint/no-explicit-any */
import { useEffect, useState } from "react";
import { Mail, IdCard, User, CircleCheck, UserX } from "lucide-react";
import type { Supervisor } from "../types/user";
import api from "../lib/api";

// import type { Student } from "../types/user";
interface AssignedStudent {
  id: string | number;
  fullName: string;
  email: string;
  matricNo: string;
  supervisor: Supervisor;
}

const AssignedStudentsList = () => {
  const [assignedStudents, setAssignedStudents] = useState<AssignedStudent[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    const fetchAssignedStudents = async () => {
      try {
        const res = await api.get("/api/assigned-students/");

        if (res.status !== 200) {
          throw new Error("Failed to fetch supervisors");
        }

        console.log("Assigned students fetched:", res.data);

        const mapped = res.data.map((stu: any) => ({
          id: stu.id,
          fullName: stu.full_name,
          email: stu.email,
          matricNo: stu.matric_no,
          supervisor: {
            id: stu.supervisor.id,
            fullName: stu.supervisor.full_name,
            email: stu.supervisor.email,
          },
        }));

        setAssignedStudents(mapped);
      } catch (err: any) {
        setError(err.message || "Something went wrong");
      } finally {
        setLoading(false);
      }
    };

    fetchAssignedStudents();
  }, []);


  if (loading)
    return (
      <div className="p-4 text-center text-gray-700 dark:text-gray-200">
        Loading supervisors...
      </div>
    );

  if (error) return <div className="p-4 text-center text-red-500">{error}</div>;

  // Empty state
  if (!loading && assignedStudents.length === 0) {
    return (
      <div className="w-full mt-10 flex flex-col items-center text-center text-gray-600 ">
        <UserX
          size={60}
          className="text-gray-500  mb-4"
        />
        <h3 className="text-xl font-semibold">No Assigned Students</h3>
        <p className="text-sm mt-2">No students have been assigned.</p>
      </div>
    );
  }

  return (
    <div className="w-full mt-6">
      <h3 className="text-xl font-bold mb-4 text-gray-900 ">
        Assigned Students
      </h3>

      {/* Desktop table */}
      <div className="hidden md:block">
        <table className="w-full border border-gray-700 rounded-lg overflow-hidden">
          <thead className="bg-green-700">
            <tr>
              <th className="p-3 text-left text-gray-200">Full Name</th>
              <th className="p-3 text-left text-gray-200">Matric No</th>
              <th className="p-3 text-left text-gray-200">Supervisor</th>
              <th className="p-3 text-left text-gray-200">Project</th>
            </tr>
          </thead>
          <tbody>
            {assignedStudents.map((sup) => (
              <tr
                key={sup.id}
                className="border-b  border-gray-700 hover:bg-gray-200  transition"
              >
                <td className="p-3">{sup.fullName}</td>
                <td className="p-3">{sup.matricNo}</td>
                <td className="p-3">{sup.supervisor.fullName}</td>
                <td className="p-3">
                  <button
                    // onClick={() => handleApprove(sup.id)}
                    // disabled={approving === sup.id}
                    className="flex items-center cursor-pointer gap-1 bg-red-600 hover:bg-red-700 text-white px-3 py-1 rounded-lg text-sm font-medium transition disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    {/* <CircleCheck size={16} /> */} NIL
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Mobile cards */}
      <div className="md:hidden grid gap-4">
        {assignedStudents.map((sup) => (
          <div
            key={sup.id}
            className="rounded-lg p-4 bg-white dark:bg-gray-900 shadow"
          >
            <div className="flex items-center gap-2 mb-2">
              <User
                size={18}
                className="text-gray-700 dark:text-gray-200"
              />
              <h4 className="font-semibold text-gray-900 dark:text-gray-100">
                {sup.fullName}
              </h4>
            </div>

            <div className="flex items-center gap-2 text-sm mb-1">
              <Mail
                size={16}
                className="text-gray-600 dark:text-gray-300"
              />
              <span className="text-gray-700 dark:text-gray-300">
                {sup.email}
              </span>
            </div>

            <div className="flex items-center gap-2 text-sm mb-3">
              <IdCard
                size={16}
                className="text-gray-600 dark:text-gray-300"
              />
              <span className="text-gray-700 dark:text-gray-300">
                {sup.matricNo}
              </span>
            </div>

            <button
              //   onClick={() => handleApprove(sup.id)}
              //   disabled={approving === sup.id}
              className="ml-8 flex items-center gap-1 w-full cursor-pointer justify-center bg-green-600 hover:bg-green-700 text-white px-3 py-2 rounded-lg text-sm font-medium transition disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <CircleCheck size={16} />
            </button>
          </div>
        ))}
      </div>
    </div>
  );
};

export default AssignedStudentsList;
