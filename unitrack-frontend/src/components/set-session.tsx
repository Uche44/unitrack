import React, { useState } from "react";
import api from "../lib/api";
import { useSessionStore } from "../context/session-context";

interface CreateSessionProps {
  closeModal: () => void;
}

const CreateSession = ({ closeModal }: CreateSessionProps) => {
  const setSessionInStore = useSessionStore((state) => state.setSession);
  const [session, setSession] = useState("");
  const [duration, setDuration] = useState("");
  const [startDate, setStartDate] = useState("");
  const [endDate, setEndDate] = useState("");

  const [loading, setLoading] = useState(false);
  const [successMsg, setSuccessMsg] = useState("");
  const [errorMsg, setErrorMsg] = useState("");

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!session || !duration || !startDate || !endDate) {
      setErrorMsg("All fields are required.");
      return;
    }

    setLoading(true);
    setErrorMsg("");
    setSuccessMsg("");

    try {
      const res = await api.post("/api/projects/session/", {
        session,
        duration,
        start_date: startDate,
        end_date: endDate,
      });

      if (res.status === 201) {
        setSuccessMsg("Session created successfully!");

        // Update Zustand store
        setSessionInStore({
          session,
          duration,
          start_date: startDate,
          end_date: endDate,
        });

        // Reset the form
        setSession("");
        setDuration("");
        setStartDate("");
        setEndDate("");

        // Close modal after success
        setTimeout(() => closeModal(), 1500);
      } else {
        setErrorMsg(res.data.error || "Failed to create session.");
      }
    } catch (err) {
      setErrorMsg("Network error. Try again.");
      console.log("error creating session:", err);
    }

    setLoading(false);
  };

  return (
    // <div className="min-h-screen px-4 flex justify-center items-center">
    <div
      onClick={(e) => e.stopPropagation()}
      className="w-full md:w-[40%] max-w-xl bg-gray-100 rounded-xl shadow-lg p-8 border border-green-200"
    >
      <h1 className="text-xl font-bold text-green-700 mb-4 text-center">
        Create Project Session
      </h1>

      {successMsg && (
        <div className="bg-gray-100 border border-green-400 text-green-700 px-4 py-3 rounded mb-4">
          {successMsg}
        </div>
      )}

      {errorMsg && (
        <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded mb-4">
          {errorMsg}
        </div>
      )}

      <form
        className="space-y-6"
        onSubmit={handleSubmit}
      >
        <div>
          <label className="block text-green-700 font-medium mb-1">
            Session
          </label>
          <input
            type="text"
            placeholder="2024/2025"
            value={session}
            onChange={(e) => setSession(e.target.value)}
            className="w-full outline-none border border-green-300 rounded-lg p-3 focus:ring-2 focus:ring-green-500"
          />
        </div>

        <div>
          <label className="block text-green-700 font-medium mb-1">
            Duration
          </label>
          <input
            type="text"
            placeholder="8 months"
            value={duration}
            onChange={(e) => setDuration(e.target.value)}
            className="w-full outline-none border border-green-300 rounded-lg p-3 focus:ring-2 focus:ring-green-500"
          />
        </div>

        <div>
          <label className="block text-green-700 font-medium mb-1">
            Start Date
          </label>
          <input
            type="date"
            value={startDate}
            onChange={(e) => setStartDate(e.target.value)}
            className="w-full border outline-none border-green-300 rounded-lg p-3 focus:ring-2 focus:ring-green-500"
          />
        </div>

        <div>
          <label className="block text-green-700 font-medium mb-1">
            End Date
          </label>
          <input
            type="date"
            value={endDate}
            onChange={(e) => setEndDate(e.target.value)}
            className="w-full border outline-none border-green-300 rounded-lg p-3 focus:ring-2 focus:ring-green-500"
          />
        </div>

        <button
          type="submit"
          disabled={loading}
          className="w-full bg-green-700 cursor-pointer text-white font-semibold py-3 rounded-xl hover:bg-green-600 transition disabled:opacity-50"
        >
          {loading ? "Creating..." : "Create Session"}
        </button>
      </form>
    </div>
    // </div>
  );
};

export default CreateSession;
