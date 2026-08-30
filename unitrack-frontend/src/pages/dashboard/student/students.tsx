import React from "react";
import { useUserStore } from "../../../context/user-context";
import api from "../../../lib/api";
import { useEffect, useState } from "react";
import type { StudentResponse } from "../../../types/student";
import { camelize } from "../../../types/camelize";
import { useSessionStore } from "../../../context/session-context";
import CreateSubmissions from "../../../components/create-submissions";
// import GuestBanner from "../../../components/guest-banner";

const Students: React.FC = () => {
  const user = useUserStore((state) => state.user);
  const [student, setStudent] = useState<StudentResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const currentSession = useSessionStore((state) => state.currentSession);

  const student_id = user?.id;

  useEffect(() => {
    const fetchStudentDetails = async () => {
      try {
        const res = await api.get(`/api/students/${student_id}/`);
        setStudent(camelize(res.data));
      } catch (error) {
        console.error("Failed to fetch student:", error);
      } finally {
        setLoading(false);
      }
    };

    if (student_id) fetchStudentDetails();
  }, [student_id]);

  if (loading)
    return (
      <div className="flex justify-center items-center h-screen text-lg font-semibold">
        Loading student details...
      </div>
    );

  if (!student)
    return (
      <div className="flex justify-center items-center h-screen text-lg text-red-500">
        No student data found.
      </div>
    );

  return (
    <section className="py-6 max-w-4xl mx-auto">
      {/* <GuestBanner /> */}
      <div className="w-full items-center flex flex-col gap-2 md:flex-row md:justify-between mt-4 mb-6">
        <h1 className="text-2xl md:text-3xl font-bold text-green-800">
          Welcome, {student?.fullName ?? user?.fullname ?? "Guest"}! 🎉
        </h1>
        <div className="space-y-1 text-sm text-green-700">
          <p>
            <span className="font-semibold">Session:</span>{" "}
            {currentSession?.session ?? "No session set"}
          </p>
        </div>
      </div>

      <div className="">
        {/* STUDENT CARD */}
        <div className="bg-white shadow-lg border-dashed border-green-600 border rounded-lg p-6 mb-8">
          <h2 className="text-2xl font-semibold text-green-700 mb-4">
            Your Details
          </h2>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-gray-700">
            <p>
              <span className="font-semibold">Full Name:</span>{" "}
              {student.fullName}
            </p>
            <p>
              <span className="font-semibold">Matric No:</span>{" "}
              {student.matricNo}
            </p>
            <p>
              <span className="font-semibold">Email:</span> {student.email}
            </p>
            <p>
              <span className="font-semibold">Department:</span>{" "}
              {student.department}
            </p>
            <p>
              <span className="font-semibold">Role:</span> {student.role}
            </p>
            <p>
              <span className="font-semibold">Joined:</span>{" "}
              {new Date(student.createdAt).toLocaleDateString()}
            </p>
          </div>
        </div>

        {/* SUPERVISOR CARD */}
        <div className="bg-gray-50 shadow-md border-dashed border-green-600 rounded-lg p-6 border border-gray-200">
          <h2 className="text-2xl font-semibold text-green-700 mb-4">
            Supervisor Details
          </h2>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-gray-800">
            <p>
              <span className="font-semibold">Full Name:</span>{" "}
              {student?.supervisor?.fullName ?? "No supervisor assigned"}
            </p>
            <p>
              <span className="font-semibold">Email:</span>{" "}
              {student?.supervisor?.email ?? "-"}
            </p>
            <p>
              <span className="font-semibold">Staff ID:</span>{" "}
              {student?.supervisor?.staffId ?? "-"}
            </p>
            <p>
              <span className="font-semibold">Status:</span>{" "}
              {student?.supervisor?.isApproved ? (
                <span className="text-green-600 font-semibold">Approved ✔</span>
              ) : (
                <span className="text-red-500 font-semibold">
                  Not Approved ✖
                </span>
              )}
            </p>
          </div>
        </div>
      </div>

      {/* add submission */}
      <CreateSubmissions />
    </section>
  );
};

export default Students;
