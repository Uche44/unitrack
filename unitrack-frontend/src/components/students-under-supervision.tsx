/* eslint-disable @typescript-eslint/no-explicit-any */
import { useEffect, useState } from "react";
import { Ellipsis } from "lucide-react";
import api from "../lib/api";
import type { Student } from "../types/user";
import { useNavigate } from "react-router-dom";

interface Props {
  supervisorId: number | undefined;
}

const StudentsUnderSupervision: React.FC<Props> = ({ supervisorId }) => {
  const [students, setStudents] = useState<Student[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [menuOpen, setMenuOpen] = useState<number | null>(null);
  const navigate = useNavigate();

useEffect(() => {
  const fetchStudents = async () => {
    try {
      setLoading(true);

      const res = await api.get(`/api/supervisors/${supervisorId}/students/`);

      const mapped = res.data.map((stu: any) => ({
        id: stu.id,
        fullName: stu.full_name,
        email: stu.email,
        matricNo: stu.matric_no,
      }));

      setStudents(mapped);
    } catch (err: any) {
      setError(err.message || "Failed to fetch students");
    } finally {
      setLoading(false);
    }
  };

  fetchStudents();
}, [supervisorId]);


  const handleReject = async (studentId: number) => {
    if (!confirm("Are you sure you want to reject this student?")) return;

    try {
      const res = await api.post(`/api/students/${studentId}/reject/`);
      if (res.status === 200) {
        setStudents((prev) => prev.filter((s) => s.id !== studentId));
      }
    } catch (err: any) {
      alert(err.message || "Failed to reject student");
    }
  };

  if (loading) {
    return (
      <div className="p-4 text-center text-gray-700">Loading students...</div>
    );
  }

  if (error) {
    return <div className="p-4 text-center text-red-500">{error}</div>;
  }

  if (students.length === 0) {
    return (
      <div className="w-full mt-10 flex flex-col items-center text-center text-gray-600">
        <h3 className="text-xl font-semibold">No Assigned Students</h3>
        <p className="text-sm mt-1">
          This supervisor currently has no students.
        </p>
      </div>
    );
  }

  return (
    <div className="w-full mt-6">
      <h3 className="text-2xl font-bold mb-4 text-green-700">
        Your Assigned Students
      </h3>

      {/* Desktop Table */}
      <div className="hidden md:block bg-white rounded-lg shadow overflow-hidden">
        <table className="w-full">
          <thead className="bg-green-700">
            <tr>
              <th className="p-3 text-left text-gray-100">Full Name</th>
              <th className="p-3 text-left text-gray-100">Email</th>
              <th className="p-3 text-left text-gray-100">Matric No</th>
              <th className="p-3 text-left text-gray-100"></th>
            </tr>
          </thead>

          <tbody>
            {students.map((student) => (
              <tr
                key={student.id}
                className="border-b border-gray-300 hover:bg-green-50 transition"
              >
                <td className="p-3">{student.fullName}</td>
                <td className="p-3">{student.email}</td>
                <td className="p-3">{student.matricNo}</td>

                <td className="p-3 relative">
                  {/* Ellipsis menu */}
                  <button
                    onClick={() =>
                      setMenuOpen(menuOpen === student.id ? null : student.id)
                    }
                    className="p-2 rounded hover:bg-gray-200"
                  >
                    <Ellipsis
                      size={20}
                      className="text-gray-700"
                    />
                  </button>

                  {menuOpen === student.id && (
                    <div className="absolute right-6 top-2 bg-white border shadow-md rounded-md w-40 z-20">
                      <button
                        onClick={() =>
                          navigate(
                            `/supervisor-dashboard/supervisors/${supervisorId}/students/${student.id}`
                          )
                        }
                        className="block w-full text-left px-4 py-2 hover:bg-gray-100"
                      >
                        View Details
                      </button>

                      <button
                        onClick={() => handleReject(student.id)}
                        className="block w-full text-left px-4 py-2 text-red-600 hover:bg-red-50"
                      >
                        Reject
                      </button>
                    </div>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Mobile Cards */}
      <div className="md:hidden space-y-4">
        {students.map((student) => (
          <div
            key={student.id}
            className="bg-white shadow p-4 rounded-lg"
          >
            <h4 className="font-semibold text-gray-900 text-lg">
              {student.fullName}
            </h4>

            <p className="text-gray-700 text-sm mt-1">{student.email}</p>
            <p className="text-gray-700 text-sm mt-1">
              Matric No: {student.matricNo}
            </p>

            <div className="flex justify-end mt-2 relative">
              <button
                onClick={() =>
                  setMenuOpen(menuOpen === student.id ? null : student.id)
                }
                className="p-2 rounded hover:bg-gray-200"
              >
                <Ellipsis
                  size={20}
                  className="text-gray-700"
                />
              </button>

              {menuOpen === student.id && (
                <div className="absolute right-0 top-10 bg-white border shadow-md rounded-md w-40 z-20">
                  <button
                    onClick={() =>
                      navigate(
                        `/supervisor-dashboard/supervisors/${supervisorId}/students/${student.id}`
                      )
                    }
                    className="block w-full text-left px-4 py-2 hover:bg-gray-100"
                  >
                    View Details
                  </button>

                  <button
                    onClick={() => handleReject(student.id)}
                    className="block w-full text-left px-4 py-2 text-red-600 hover:bg-red-50"
                  >
                    Reject
                  </button>
                </div>
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

export default StudentsUnderSupervision;
