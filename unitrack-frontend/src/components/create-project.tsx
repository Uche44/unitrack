/* eslint-disable @typescript-eslint/no-explicit-any */
import React, { useState } from "react";
import toast from "react-hot-toast";
import api from "../lib/api";
import { useSubmissionStore } from "../context/submission-context";

interface CreateProjectProps {
  setOpenProjectModal: (open: boolean) => void;
  setOpenSubmissionModal: (open: boolean) => void;
}

const CreateProject: React.FC<CreateProjectProps> = ({
  setOpenProjectModal,
  setOpenSubmissionModal,
}) => {
  const [projectData, setProjectData] = useState({
    title: "",
    description: "",
  });

  const { loading, setLoading, setProjectId } = useSubmissionStore();

  const createProject = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);

    try {
      const res = await api.post("/api/projects/create/", {
        title: projectData.title,
        description: projectData.description,
      });

      const createdProjectId = res.data.project.id;

      setProjectId(createdProjectId);
      toast.success("Project created successfully");

      setOpenProjectModal(false);
      setOpenSubmissionModal(true);
    } catch (err: any) {
      const message =
        err?.response?.data?.error ||
        err?.response?.data?.detail ||
        "Project creation failed";

      toast.error(message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <section className="w-full h-screen bg-white">
      <h2 className="text-2xl font-bold text-green-700 mb-4">Create Project</h2>

      <form
        onSubmit={createProject}
        className="space-y-4"
      >
        <input
          required
          placeholder="Project Title"
          className="w-full border border-green-500 rounded-md px-3 py-2"
          onChange={(e) =>
            setProjectData({ ...projectData, title: e.target.value })
          }
        />

        <textarea
          required
          placeholder="Project Description"
          rows={4}
          className="w-full border border-green-500 rounded-md px-3 py-2"
          onChange={(e) =>
            setProjectData({
              ...projectData,
              description: e.target.value,
            })
          }
        />

        <button
          disabled={loading}
          className="w-full bg-green-700 text-white py-2 rounded-md disabled:opacity-60"
        >
          {loading ? "Creating..." : "Create Project"}
        </button>
      </form>
    </section>
  );
};

export default CreateProject;
