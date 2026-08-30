/* eslint-disable @typescript-eslint/no-explicit-any */
import { useEffect, useState } from "react";
import { Mail, IdCard, User, CircleCheck, UserX } from "lucide-react";
import type { Supervisor } from "../types/user";
import api from "../lib/api";
import { camelize } from "../types/camelize";

const PendingSupervisorsList = () => {
  const [pendingSupervisors, setPendingSupervisors] = useState<Supervisor[]>(
    []
  );
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [approving, setApproving] = useState<string | null>(null);

  useEffect(() => {
    const fetchSupervisors = async () => {
      try {
        const res = await api.get("/api/pending");
        if (res.status === 200) {
          console.log("Supervisors fetched:", res.data);
        } else {
          throw new Error("Failed to fetch supervisors");
        }

        setPendingSupervisors(camelize(res.data));
      } catch (err: any) {
        setError(err.message || "Something went wrong");
      } finally {
        setLoading(false);
      }
    };

    fetchSupervisors();
  }, []);

  const handleApprove = async (id: string) => {
    try {
      setApproving(id);
      const res = await api.post(
        `/api/supervisors/${id}/approve/`,
        {},
        {
          withCredentials: true,
        }
      );
      if (res.status === 200) {
        // remove approved supervisor
        setPendingSupervisors((prev) =>
          prev.filter((sup) => sup.id !== parseInt(id))
        );
      } else {
        throw new Error("Approval failed");
      }
    } catch (err: any) {
      alert(err.message || "Something went wrong");
      console.log(err.message);
    } finally {
      setApproving(null);
    }
  };

  if (loading)
    return (
      <div className="p-4 text-center text-gray-700 dark:text-gray-200">
        Loading supervisors...
      </div>
    );

  if (error) return <div className="p-4 text-center text-red-500">{error}</div>;

  if (!loading && pendingSupervisors.length === 0) {
    return (
      <div className="w-full mt-10 flex flex-col items-center text-center text-gray-600 ">
        <UserX
          size={60}
          className="text-gray-500  mb-4"
        />
        <h3 className="text-xl font-semibold">No Pending Registrations</h3>
        <p className="text-sm mt-2">All supervisors have been approved.</p>
      </div>
    );
  }

  return (
    <div className="w-full mt-6">
      <h3 className="text-xl font-bold mb-4 text-gray-900 ">
        Pending Supervisors
      </h3>

      {/* Desktop table */}
      <div className="hidden md:block">
        <table className="w-full border border-gray-700 rounded-lg overflow-hidden">
          <thead className="bg-red-700">
            <tr>
              <th className="p-3 text-left text-gray-200">Full Name</th>
              <th className="p-3 text-left text-gray-200">Email</th>
              <th className="p-3 text-left text-gray-200">Staff ID</th>
              <th className="p-3 text-left text-gray-200"></th>
            </tr>
          </thead>
          <tbody>
            {pendingSupervisors.map((sup) => (
              <tr
                key={sup.id}
                className="border-b  border-gray-700 hover:bg-gray-200  transition"
              >
                <td className="p-3">{sup.fullName}</td>
                <td className="p-3">{sup.email}</td>
                <td className="p-3">{sup.staffId}</td>
                <td className="p-3">
                  <button
                    onClick={() => handleApprove(String(sup.id))}
                    disabled={approving === String(sup.id)}
                    className="flex items-center cursor-pointer gap-1 bg-green-600 hover:bg-green-700 text-white px-3 py-1 rounded-lg text-sm font-medium transition disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    <CircleCheck size={16} /> Approve
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Mobile cards */}
      <div className="md:hidden grid gap-4">
        {pendingSupervisors.map((sup) => (
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

            <button
              onClick={() => handleApprove(String(sup.id))}
              disabled={approving === String(sup.id)}
              className="ml-8 flex items-center gap-1 w-full cursor-pointer justify-center bg-green-600 hover:bg-green-700 text-white px-3 py-2 rounded-lg text-sm font-medium transition disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <CircleCheck size={16} /> Approve
            </button>
          </div>
        ))}
      </div>
    </div>
  );
};

export default PendingSupervisorsList;
