import React, { useCallback, useEffect, useState } from "react";
import { useSearchParams } from "react-router-dom";
import api from "../../../lib/api";
import type { Student, Supervisor } from "../../../types/user";
import { camelize } from "../../../types/camelize";
import { useGuestMode } from "../../../hooks/useGuestMode";
import GuestBanner from "../../../components/guest-banner";

interface StudentSuggestion {
  student_id: number;
  full_name: string;
  matric_no?: string;
  project_interests?: string;
  matched_keywords?: string[];
  reasoning?: string;
  expertise_score?: number;
}

const AssignSupervisor: React.FC = () => {
  const [students, setStudents] = useState<Student[]>([]);
  const [supervisors, setSupervisors] = useState<Supervisor[]>([]);
  const [selected, setSelected] = useState<number[]>([]);
  const [loading, setLoading] = useState(false);
  const [supervisorModalOpen, setSupervisorModalOpen] = useState(false);
  const [studentModalOpen, setStudentModalOpen] = useState(false);
  const [chosenSupervisor, setChosenSupervisor] = useState<number | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);
  const [successModalOpen, setSuccessModalOpen] = useState(false);
  const { isGuest } = useGuestMode();
  const [searchParams, setSearchParams] = useSearchParams();
  const highlightId = Number(searchParams.get("highlight") ?? "0") || null;
  const [recommendationNote, setRecommendationNote] = useState<string | null>(null);
  const [suggestions, setSuggestions] = useState<StudentSuggestion[]>([]);
  const [suggestionLoading, setSuggestionLoading] = useState(false);
  const [suggestionError, setSuggestionError] = useState<string | null>(null);

  useEffect(() => {
    fetchData();
  }, []);

  useEffect(() => {
    if (!highlightId) return;
    setSupervisorModalOpen(true);
    setChosenSupervisor(highlightId);
    setRecommendationNote(
      `Recommended supervisor (id ${highlightId}) highlighted. Review the reasoning and confirm before assigning.`,
    );
  }, [highlightId]);

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

  function chooseSupervisor(id: number) {
    if (isGuest) return;
    setChosenSupervisor(id);
    setSelected([]);
    setSupervisorModalOpen(false);
    setStudentModalOpen(true);
  }

  const loadSuggestions = useCallback(async (supervisorId: number) => {
    setSuggestionLoading(true);
    setSuggestionError(null);
    setSuggestions([]);
    try {
      const response = await api.get<{ candidates: StudentSuggestion[] }>(
        "/api/suggest-supervisor/",
        { params: { supervisor_id: supervisorId, limit: 5 } },
      );
      const ranked = response.data.candidates ?? [];
      setSuggestions(ranked);
      const seedIds = ranked
        .slice(0, Math.min(5, ranked.length))
        .map((s) => s.student_id);
      if (seedIds.length > 0) setSelected(seedIds);
    } catch (caught: unknown) {
      const message =
        (caught as { response?: { data?: { error?: string } } })?.response?.data
          ?.error ?? "Failed to load suggestions.";
      setSuggestionError(message);
    } finally {
      setSuggestionLoading(false);
    }
  }, []);

  useEffect(() => {
    if (!studentModalOpen || !chosenSupervisor) return;
    loadSuggestions(chosenSupervisor);
  }, [studentModalOpen, chosenSupervisor, loadSuggestions]);

  function toggleStudent(id: number) {
    if (isGuest) return;
    setSelected((prev) => {
      if (prev.includes(id)) return prev.filter((x) => x !== id);
      if (prev.length >= 5) return prev;
      return [...prev, id];
    });
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
      setSuccessMessage(
        `${supervisor?.fullName} has been assigned to ${
          selected.length
        } student${selected.length > 1 ? "s" : ""}.`,
      );
      setSuccessModalOpen(true);

      setStudents((prev) => prev.filter((s) => !selected.includes(s.id)));
      setSupervisors((prev) => prev.filter((p) => p.id !== chosenSupervisor));
      setSelected([]);
      setStudentModalOpen(false);
      setSuggestions([]);
      setError(null);
    } catch (err: unknown) {
      console.error(err as Error);
      setError("Failed to assign. Try again.");
    } finally {
      setLoading(false);
    }
  }

  const chosenSupervisorRecord = supervisors.find(
    (sup) => sup.id === chosenSupervisor,
  );

  return (
    <div className="p-4 md:p-8 max-w-6xl mx-auto">
      <GuestBanner />
      <div className="flex items-center justify-between my-6 ">
        <h1 className="text-2xl font-bold text-green-700">Assign Supervisors</h1>

        <div className="flex items-center gap-3">
          <div className="text-sm text-gray-600">
            Supervisor:{" "}
            <span className="font-semibold">
              {chosenSupervisorRecord?.fullName ?? "Not selected"}
            </span>
          </div>
          <button
            onClick={() => setSupervisorModalOpen(true)}
            disabled={isGuest}
            className={`px-4 py-2 rounded-md text-white ${
              isGuest
                ? "bg-gray-400 cursor-not-allowed"
                : "bg-green-600 disabled:opacity-60 disabled:cursor-not-allowed"
            }`}
          >
            {chosenSupervisor ? "Change supervisor" : "Pick a supervisor"}
          </button>
        </div>
      </div>

      {error && (
        <div className="mb-4 text-sm text-red-700 bg-red-100 p-2 rounded">
          {error}
        </div>
      )}

      <div className="bg-white rounded shadow overflow-x-auto">
        <table className="min-w-full">
          <thead className="bg-green-50">
            <tr>
              <th className="p-3 text-left">Fullname</th>
              <th className="p-3 text-left">Email</th>
              <th className="p-3 text-left">Matric No</th>
              <th className="p-3 text-left">Status</th>
            </tr>
          </thead>
          <tbody>
            {loading && (
              <tr>
                <td colSpan={4} className="p-6 text-center text-gray-500">
                  Loading...
                </td>
              </tr>
            )}

            {!loading && students.length === 0 && (
              <tr>
                <td colSpan={4} className="p-6 text-center text-gray-500">
                  No available students to assign.
                </td>
              </tr>
            )}

            {students.map((s) => (
              <tr key={s.id} className="border-t border-gray-500">
                <td className="p-3">{s.fullName}</td>
                <td className="p-3">{s.email}</td>
                <td className="p-3">{s.matricNo || "-"}</td>
                <td className="p-3 text-gray-500">Waiting</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Supervisor picker modal */}
      {supervisorModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
          <div
            className="absolute inset-0 bg-black opacity-30"
            onClick={() => setSupervisorModalOpen(false)}
          />
          <div className="relative bg-white rounded-lg shadow-lg w-full max-w-2xl">
            <div className="flex items-center justify-between p-4 border-b">
              <h2 className="text-lg font-medium text-green-700">
                Choose supervisor
              </h2>
              {recommendationNote && (
                <span className="text-xs text-purple-700 font-semibold">
                  {recommendationNote}
                </span>
              )}
              <button
                onClick={() => {
                  setSupervisorModalOpen(false);
                  if (highlightId) {
                    const next = new URLSearchParams(searchParams);
                    next.delete("highlight");
                    setSearchParams(next, { replace: true });
                    setRecommendationNote(null);
                  }
                }}
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
                    } ${
                      highlightId === sup.id
                        ? "ring-2 ring-purple-400 ring-offset-1"
                        : ""
                    }`}
                  >
                    <div>
                      <div className="font-medium">
                        {sup.fullName}
                        {highlightId === sup.id && (
                          <span className="ml-2 text-xs text-purple-700 font-semibold">
                            Recommended
                          </span>
                        )}
                      </div>
                      <div className="text-sm text-gray-500">{sup.email}</div>
                    </div>
                    <button
                      onClick={() => chooseSupervisor(sup.id)}
                      disabled={isGuest}
                      className="px-3 py-1 text-sm rounded bg-green-600 text-white hover:bg-green-700 disabled:opacity-50"
                    >
                      Select
                    </button>
                  </li>
                ))}
              </ul>
            </div>

            <div className="flex items-center justify-end gap-3 p-4 border-t">
              <button
                onClick={() => setSupervisorModalOpen(false)}
                className="px-4 py-2 rounded bg-white border"
              >
                Cancel
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Student picker modal driven by suggest_supervisor_assignment */}
      {studentModalOpen && chosenSupervisor && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
          <div
            className="absolute inset-0 bg-black opacity-30"
            onClick={() => setStudentModalOpen(false)}
          />
          <div className="relative bg-white rounded-lg shadow-lg w-full max-w-3xl">
            <div className="flex items-center justify-between p-4 border-b">
              <div>
                <h2 className="text-lg font-medium text-green-700">
                  Pick students for {chosenSupervisorRecord?.fullName}
                </h2>
                <p className="text-xs text-gray-500">
                  Top suggestions from the agent are pre-selected. Untick any
                  you don't want before clicking Assign.
                </p>
              </div>
              <div className="flex items-center gap-3">
                <span className="text-xs text-gray-600">
                  Selected: {selected.length}/5
                </span>
                <button
                  onClick={() => {
                    setStudentModalOpen(false);
                    setSelected([]);
                    setSuggestions([]);
                  }}
                  className="text-gray-500"
                >
                  ✕
                </button>
              </div>
            </div>

            <div className="p-4 max-h-[28rem] overflow-auto">
              {suggestionLoading && (
                <div className="text-sm text-gray-500">
                  Asking the agent for matching students...
                </div>
              )}
              {suggestionError && (
                <div className="text-sm text-red-700 bg-red-100 p-2 rounded mb-2">
                  {suggestionError}
                </div>
              )}

              {!suggestionLoading && !suggestionError && (
                <>
                  {suggestions.length > 0 && (
                    <div className="mb-4">
                      <h3 className="text-sm font-semibold text-purple-700 mb-2">
                        Agent suggestions
                      </h3>
                      <ul className="space-y-2">
                        {suggestions.map((s) => (
                          <li
                            key={s.student_id}
                            className={`p-3 rounded border ${
                              selected.includes(s.student_id)
                                ? "border-green-600 bg-green-50"
                                : "border-gray-200"
                            }`}
                          >
                            <div className="flex items-start gap-3">
                              <input
                                type="checkbox"
                                checked={selected.includes(s.student_id)}
                                disabled={isGuest}
                                onChange={() => toggleStudent(s.student_id)}
                                className="mt-1 h-4 w-4 text-green-600"
                              />
                              <div className="flex-1">
                                <div className="font-medium">
                                  {s.full_name}
                                  <span className="ml-2 text-xs text-gray-500">
                                    {s.matric_no ?? ""}
                                  </span>
                                </div>
                                <div className="text-xs text-gray-500 mb-1">
                                  Interests: {s.project_interests ?? "(not set)"}
                                </div>
                                <p className="text-xs text-gray-600">
                                  {s.reasoning}
                                </p>
                              </div>
                            </div>
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}

                  <div>
                    <h3 className="text-sm font-semibold text-gray-700 mb-2">
                      All unassigned students
                    </h3>
                    <ul className="space-y-2">
                      {students
                        .filter(
                          (s) => !suggestions.some((sg) => sg.student_id === s.id),
                        )
                        .map((s) => (
                          <li
                            key={s.id}
                            className={`p-3 rounded border ${
                              selected.includes(s.id)
                                ? "border-green-600 bg-green-50"
                                : "border-gray-200"
                            }`}
                          >
                            <div className="flex items-start gap-3">
                              <input
                                type="checkbox"
                                checked={selected.includes(s.id)}
                                disabled={
                                  (!selected.includes(s.id) &&
                                    selected.length >= 5) ||
                                  isGuest
                                }
                                onChange={() => toggleStudent(s.id)}
                                className="mt-1 h-4 w-4 text-green-600"
                              />
                              <div className="flex-1">
                                <div className="font-medium">{s.fullName}</div>
                                <div className="text-xs text-gray-500">
                                  {s.email} · {s.matricNo || "-"}
                                </div>
                              </div>
                            </div>
                          </li>
                        ))}
                    </ul>
                  </div>
                </>
              )}
            </div>

            <div className="flex items-center justify-end gap-3 p-4 border-t">
              <button
                onClick={() => {
                  setStudentModalOpen(false);
                  setSelected([]);
                  setSuggestions([]);
                }}
                className="px-4 py-2 rounded bg-white border"
              >
                Cancel
              </button>
              <button
                onClick={assign}
                disabled={
                  !chosenSupervisor ||
                  selected.length === 0 ||
                  loading ||
                  isGuest
                }
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
                onClick={() => {
                  setSuccessModalOpen(false);
                  if (highlightId) {
                    const next = new URLSearchParams(searchParams);
                    next.delete("highlight");
                    setSearchParams(next, { replace: true });
                  }
                }}
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
