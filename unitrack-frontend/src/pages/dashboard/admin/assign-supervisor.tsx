/* eslint-disable @typescript-eslint/no-unused-vars */
import React, { useEffect, useState } from "react";
import api from "../../../lib/api";
import type { Student, Supervisor } from "../../../types/user";
import { camelize } from "../../../types/camelize";
import { useGuestMode } from "../../../hooks/useGuestMode";
import GuestBanner from "../../../components/guest-banner";

const AssignSupervisor: React.FC = () => {
  const [students, setStudents] = useState<Student[]>([]);
  const [supervisors, setSupervisors] = useState<Supervisor[]>([]);
  const [selected, setSelected] = useState<number[]>([]);
  const [loading, setLoading] = useState(false);
  const [modalOpen, setModalOpen] = useState(false);
  const [chosenSupervisor, setChosenSupervisor] = useState<number | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);
  const [_assignedSupervisorName, setAssignedSupervisorName] = useState<
    string | null
  >(null);
  const [_assignedCount, setAssignedCount] = useState<number>(0);
  const [successModalOpen, setSuccessModalOpen] = useState(false);
  const { isGuest } = useGuestMode();

  useEffect(() => {
    fetchData();
  }, []);

  async function fetchData() {
    try {
      setLoading(true);
      const [sRes, supRes] = await Promise.all([
        api.get("/api/students/"),
        api.get("/api/supervisors/"),
      ]);

      setStudents(camelize(sRes.data) || []);
      setSupervisors(camelize(supRes.data) || []);
    } catch (err: unknown) {
      console.error(err as Error);
      setError("Failed to load data. Please refresh.");
    } finally {
      setLoading(false);
    }
  }

  function toggleStudent(id: number) {
    if (isGuest) return; // Disable for guests
    setSelected((prev) => {
      if (prev.includes(id)) return prev.filter((x) => x !== id);
      if (prev.length >= 5) return prev;
      return [...prev, id];
    });
  }

  function openModal() {
    if (isGuest) return; // Disable for guests
    setModalOpen(true);
    setChosenSupervisor(null);
  }

  async function assign() {
    if (isGuest) return; 
    if (!chosenSupervisor) return setError("Choose a supervisor first.");
    if (selected.length === 0) return setError("Choose students first.");

    try {
      setLoading(true);
      await api.post("/api/assign-supervisor/", {
        supervisor_id: chosenSupervisor,
        student_ids: selected,
      });

      const supervisor = supervisors.find((sup) => sup.id === chosenSupervisor);

      // save success info
      setAssignedSupervisorName(supervisor?.fullName || "Supervisor");
      setAssignedCount(selected.length);
      setSuccessMessage(
        `${supervisor?.fullName} has been assigned to ${
          selected.length
        } student${selected.length > 1 ? "s" : ""}.`
      );
      setSuccessModalOpen(true);

      // remove assigned students and supervisor from lists
      setStudents((prev) => prev.filter((s) => !selected.includes(s.id)));
      setSupervisors((prev) => prev.filter((p) => p.id !== chosenSupervisor));
      setSelected([]);
      setModalOpen(false);
      setError(null);
    } catch (err: unknown) {
      console.error(err as Error);
      setError("Failed to assign. Try again.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="p-4 md:p-8 max-w-6xl mx-auto">
      <GuestBanner />
      <div className="flex items-center justify-between my-6 ">
        <h1 className="text-2xl font-bold text-green-700">
          Assign Supervisors
        </h1>

        <div className="flex items-center gap-3">
          <div className="text-sm text-gray-600">
            Selected: {selected.length}/5
          </div>
          <button
            onClick={openModal}
            disabled={selected.length === 0 || isGuest}
            className={`px-4 py-2 rounded-md text-white ${
              isGuest
                ? "bg-gray-400 cursor-not-allowed"
                : "bg-green-600 disabled:opacity-60 disabled:cursor-not-allowed"
            }`}
          >
            Choose Supervisor
          </button>
        </div>
      </div>

      <h2 className="text-gray-700 font-bold md:text-xl mb-4">
        Student Information
      </h2>

      {error && (
        <div className="mb-4 text-sm text-red-700 bg-red-100 p-2 rounded">
          {error}
        </div>
      )}

      <div className="bg-white rounded shadow overflow-x-auto">
        <table className="min-w-full">
          <thead className="bg-green-50">
            <tr>
              <th className="p-3 text-left">Select</th>
              <th className="p-3 text-left">Fullname</th>
              <th className="p-3 text-left">Email</th>
              <th className="p-3 text-left">Matric No</th>
            </tr>
          </thead>
          <tbody>
            {loading && (
              <tr>
                <td
                  colSpan={4}
                  className="p-6 text-center text-gray-500"
                >
                  Loading...
                </td>
              </tr>
            )}

            {!loading && students.length === 0 && (
              <tr>
                <td
                  colSpan={4}
                  className="p-6 text-center text-gray-500"
                >
                  No available students to assign.
                </td>
              </tr>
            )}

            {students.map((s) => {
              const disabled = !selected.includes(s.id) && selected.length >= 5;
              return (
                <tr
                  key={s.id}
                  className="border-t border-gray-500"
                >
                  <td className="p-3">
                    <input
                      type="checkbox"
                      checked={selected.includes(s.id)}
                      disabled={disabled || isGuest}
                      onChange={() => toggleStudent(s.id)}
                      className="h-4 w-4 text-green-600"
                    />
                  </td>
                  <td className="p-3">{s.fullName}</td>
                  <td className="p-3">{s.email}</td>
                  <td className="p-3">{s.matricNo || "-"}</td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>

      {/* Modal */}
      {modalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
          <div
            className="absolute inset-0 bg-black opacity-30"
            onClick={() => setModalOpen(false)}
          />
          <div className="relative bg-white rounded-lg shadow-lg w-full max-w-2xl">
            <div className="flex items-center justify-between p-4 border-b">
              <h2 className="text-lg font-medium text-green-700">
                Choose Supervisor
              </h2>
              <button
                onClick={() => setModalOpen(false)}
                className="text-gray-500"
              >
                ✕
              </button>
            </div>

            <div className="p-4 max-h-96 overflow-auto">
              {supervisors.length === 0 && (
                <div className="text-gray-600">No supervisors available.</div>
              )}

              <ul className="space-y-2">
                {supervisors.map((sup) => (
                  <li
                    key={sup.id}
                    className={`flex items-center justify-between p-3 rounded border ${
                      chosenSupervisor === sup.id
                        ? "border-green-600 bg-green-50"
                        : "border-gray-100"
                    }`}
                  >
                    <div>
                      <div className="font-medium">{sup.fullName}</div>
                      <div className="text-sm text-gray-500">{sup.email}</div>
                    </div>
                    <div className="flex items-center gap-3">
                      <input
                        type="radio"
                        name="chosenSupervisor"
                        checked={chosenSupervisor === sup.id}
                        disabled={isGuest}
                        onChange={() => setChosenSupervisor(sup.id)}
                        className="h-4 w-4 text-green-600"
                      />
                    </div>
                  </li>
                ))}
              </ul>
            </div>

            <div className="flex items-center justify-end gap-3 p-4 border-t">
              <button
                onClick={() => setModalOpen(false)}
                className="px-4 py-2 rounded bg-white border"
              >
                Cancel
              </button>
              <button
                onClick={assign}
                disabled={!chosenSupervisor || loading || isGuest}
                className={`px-4 py-2 rounded text-white ${
                  isGuest
                    ? "bg-gray-400 cursor-not-allowed"
                    : "bg-green-600 disabled:opacity-60 disabled:cursor-not-allowed"
                }`}
              >
                {loading ? "Assigning..." : "Assign"}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* success modal */}

      {/* Success Modal */}
      {successModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
          <div
            className="absolute inset-0 bg-black opacity-30"
            onClick={() => setSuccessModalOpen(false)}
          />
          <div className="relative bg-white rounded-lg shadow-lg w-full max-w-md p-6">
            <h2 className="text-lg font-medium text-green-700 mb-4">
              Supervisor Assigned Successfully!
            </h2>
            <p className="text-gray-700">{successMessage}</p>
            <div className="flex justify-end mt-6">
              <button
                onClick={() => setSuccessModalOpen(false)}
                className="px-4 py-2 rounded bg-green-600 text-white"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
export default AssignSupervisor;
