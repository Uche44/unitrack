/* eslint-disable @typescript-eslint/no-explicit-any */
import { useEffect, useState } from "react";
import { Mail, IdCard, User, Ellipsis } from "lucide-react";
import api from "../lib/api";
import type { Supervisor } from "../types/user";
// interface Supervisor {
//   id: string;
//   fullName: string;
//   email: string;
//   staffId: string;
// }

const ApprovedSupervisorsList = () => {
  const [supervisors, setSupervisors] = useState<Supervisor[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    const fetchSupervisors = async () => {
      try {
        const res = await api.get("/api/supervisors");

        if (res.status !== 200) {
          throw new Error("Failed to fetch supervisors");
        }

        const mapped = res.data.map((sup: any) => ({
          id: sup.id,
          fullName: sup.full_name,
          email: sup.email,
          staffId: sup.staff_id,
        }));

        setSupervisors(mapped);
      } catch (err: any) {
        setError(err.message || "Something went wrong");
      } finally {
        setLoading(false);
      }
    };

    fetchSupervisors();
  }, []);

  if (loading)
    return (
      <div className="p-4 text-center text-gray-700 dark:text-gray-200">
        Loading supervisors...
      </div>
    );

  if (error) return <div className="p-4 text-center text-red-500">{error}</div>;

  return (
    <div className="w-full mt-10">
      <h3 className="text-xl font-bold mb-4 text-gray-900 ">
        Approved Supervisors
      </h3>

      {/* Desktop table */}
      <div className="hidden md:block">
        <table className="w-full border border-gray-700 rounded-lg overflow-hidden">
          <thead className="bg-green-700">
            <tr>
              <th className="p-3 text-left text-gray-200">Full Name</th>
              <th className="p-3 text-left text-gray-200">Email</th>
              <th className="p-3 text-left text-gray-200">Staff ID</th>
              <th className="p-3 text-left text-gray-200"></th>
            </tr>
          </thead>
          <tbody>
            {supervisors.map((sup) => (
              <tr
                key={sup.id}
                className="border-b  border-gray-700 hover:bg-gray-200  transition"
              >
                <td className="p-3">{sup.fullName}</td>
                <td className="p-3">{sup.email}</td>
                <td className="p-3">{sup.staffId}</td>

                <td className="p-3">
                  <button className="cursor-pointer">
                    <Ellipsis size={16} />
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Mobile cards */}
      <div className="md:hidden grid gap-4">
        {supervisors.map((sup) => (
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
                {sup.staffId}
              </span>
            </div>

            <button>
              <Ellipsis size={16} />
            </button>
          </div>
        ))}
      </div>
    </div>
  );
};

export default ApprovedSupervisorsList;
