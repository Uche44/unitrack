/* eslint-disable @typescript-eslint/no-explicit-any */
import React, { useState } from "react";
import { Plus, FileText } from "lucide-react";
import toast from "react-hot-toast";
import api from "../lib/api";
import { useSubmissionStore } from "../context/submission-context";
import { useUserStore } from "../context/user-context";
// import CreateProject from "./create-project";
import { FileUpload } from "./file-upload";

const CreateSubmissions: React.FC = () => {
  const user = useUserStore((state) => state.user);
  const {
    currentStage,
    projectId,
    setProjectId,
    setCurrentStage,
    loading,
    setLoading,
  } = useSubmissionStore();

  const [openProjectModal, setOpenProjectModal] = useState(false);
  const [openSubmissionModal, setOpenSubmissionModal] = useState(false);
  const [projectStatus, setProjectStatus] = useState<string | null>(null);
  const [latestSubmissionRejected, setLatestSubmissionRejected] =
    useState(false);
  const [rejectionComment, setRejectionComment] = useState<string | null>(null);

  const [projectData, setProjectData] = useState({
    title: "",
    description: "",
  });

  const [file, setFile] = useState<File | null>(null);

  // Fetch project ID if not in store
  React.useEffect(() => {
    const fetchUserProject = async () => {
      if (!user || projectId) return;
      try {
        // Fetch all projects
        const res = await api.get("/api/projects/");

        // Filter for user's projects and sort by newest first
        const myProjects = res.data
          .filter((p: any) => p.student === user.id || p.student.id === user.id)
          .sort(
            (a: any, b: any) =>
              new Date(b.createdAt).getTime() -
              new Date(a.createdAt).getTime(),
          );

        if (myProjects.length > 0) {
          setProjectId(myProjects[0].id);
        }
      } catch (err) {
        console.log(err, "No existing project found or failed to fetch");
      }
    };

    fetchUserProject();
  }, [user, projectId, setProjectId]);

  // Fetch project status and determine current stage
  React.useEffect(() => {
    const fetchProjectStatus = async () => {
      if (projectId) {
        try {
          console.log("DEBUG: Fetching project status...");
          const res = await api.get(`/api/projects/${projectId}/`);
          console.log("DEBUG: API Response:", res.data);

          const status = res.data.status;
          const submissions = res.data.submissions || [];

          setProjectStatus(status);

          // Sort submissions by version (descending)
          const sortedSubmissions = submissions.sort(
            (a: any, b: any) => b.version - a.version,
          );

          console.log("DEBUG: Sorted Submissions:", sortedSubmissions);

          // Check status of each milestone
          const getMilestoneStatus = (milestone: string) => {
            const sub = sortedSubmissions.find(
              (s: any) => s.milestone === milestone,
            );
            return sub
              ? {
                  is_approved: sub.is_approved,
                  is_rejected: sub.is_rejected,
                  comment: sub.rejection_comment,
                }
              : null;
          };

          const proposal = getMilestoneStatus("proposal");
          const chapterOne = getMilestoneStatus("chapter_one");
          const chapterTwo = getMilestoneStatus("chapter_two");
          const finalReport = getMilestoneStatus("final_report");

          console.log("DEBUG: Computed Statuses:", {
            proposal,
            chapterOne,
            chapterTwo,
            finalReport,
          });

          // Determine current stage
          // Determine current stage
          // Sequential logic:
          // 1. If proposal not approved -> proposal
          // 2. If proposal approved AND chapterOne not approved -> chapter_one
          // 3. If chapterOne approved AND chapterTwo not approved -> chapter_two
          // 4. If chapterTwo approved -> final_report

          if (!proposal || !proposal.is_approved) {
            setCurrentStage("proposal");
            setLatestSubmissionRejected(proposal?.is_rejected || false);
            setRejectionComment(proposal?.comment || null);
          } else if (
            proposal.is_approved &&
            (!chapterOne || !chapterOne.is_approved)
          ) {
            setCurrentStage("chapter_one");
            setLatestSubmissionRejected(chapterOne?.is_rejected || false);
            setRejectionComment(chapterOne?.comment || null);
          } else if (
            chapterOne &&
            chapterOne.is_approved &&
            (!chapterTwo || !chapterTwo.is_approved)
          ) {
            setCurrentStage("chapter_two");
            setLatestSubmissionRejected(chapterTwo?.is_rejected || false);
            setRejectionComment(chapterTwo?.comment || null);
          } else if (chapterTwo && chapterTwo.is_approved) {
            setCurrentStage("final_report");
            setLatestSubmissionRejected(finalReport?.is_rejected || false);
            setRejectionComment(finalReport?.comment || null);
          }
        } catch (err) {
          console.error("Failed to fetch project status:", err);
        }
      }
    };

    fetchProjectStatus();
  }, [projectId, setCurrentStage]);

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

  const submitMilestone = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!file || !projectId) {
      toast.error("Please select a file before submitting");
      return;
    }

    setLoading(true);

    const formData = new FormData();
    formData.append("project", String(projectId));
    formData.append("milestone", currentStage);
    formData.append("file", file);

    try {
      await api.post("/api/submissions/create/", formData, {
        headers: { "Content-Type": "multipart/form-data" },
      });

      toast.success(`${currentStage.replace("_", " ")} submitted successfully`);
      // advanceStage(); // Don't auto-advance, wait for approval
      setOpenSubmissionModal(false);
      setFile(null);
      // Trigger a re-fetch of status ideally, or just let the effect update on next load
      window.location.reload();
    } catch (err: any) {
      const message =
        err?.response?.data?.error ||
        err?.response?.data?.detail ||
        "Submission failed";

      toast.error(message);
    } finally {
      setLoading(false);
    }
  };

  const getButtonText = () => {
    if (!projectId) return "Create Project";

    // If project exists, we are submitting a file, regardless of rejection status (we resubmit)
    if (latestSubmissionRejected)
      return `Resubmit ${currentStage.replace("_", " ")}`;

    return `Submit ${currentStage.replace("_", " ")}`;
  };

  const getStatusMessage = () => {
    if (latestSubmissionRejected) {
      return (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4 text-center mb-4">
          <p className="text-red-800 font-semibold">
            ✕ Your submission was rejected
          </p>
          <p className="text-red-700 text-sm mt-1">
            {rejectionComment || "Please view comments and resubmit."}
          </p>
        </div>
      );
    }
    return null;
  };

  return (
    <>
      {/* ACTION BUTTON */}
      <section className="mt-10 flex flex-col items-end">
        {getStatusMessage()}

        {/* Show button logic */}
        {(!projectId ||
          latestSubmissionRejected ||
          projectStatus !== "completed") && (
          <>
            <button
              onClick={() => {
                if (!projectId) {
                  setOpenProjectModal(true);
                } else {
                  setOpenSubmissionModal(true);
                }
              }}
              className="py-3 px-4 bg-green-700 hover:bg-green-800 text-white rounded-lg font-semibold shadow flex gap-2"
            >
              <Plus />
              {getButtonText()}
            </button>

            <p className="text-gray-600 mt-4">
              {!projectId
                ? "Start your project by submitting a proposal"
                : `Submit your ${currentStage.replace("_", " ")} to your supervisor`}
            </p>
          </>
        )}

        {projectStatus == "completed" && (
          <div className="text-center space-y-4">
            <p className="text-green-600 font-bold text-2xl">
              Congratulations! Your project is completed.
            </p>
            <button
              onClick={async () => {
                if (!projectId) return;
                try {
                  const response = await api.get(
                    `/api/projects/${projectId}/download-report/`,
                    {
                      responseType: "blob", // Important for file downloads
                    },
                  );

                  // Create a blob from the response
                  const blob = new Blob([response.data], {
                    type: "application/pdf",
                  });
                  const url = window.URL.createObjectURL(blob);

                  // Create a temporary link element
                  const link = document.createElement("a");
                  link.href = url;
                  link.download = `Project_Full_Report.pdf`; // Filename
                  document.body.appendChild(link);

                  // Trigger download
                  link.click();

                  // Cleanup
                  document.body.removeChild(link);
                  window.URL.revokeObjectURL(url);
                  toast.success("Download started!");
                } catch (error) {
                  console.error("Download failed", error);
                  toast.error("Failed to download report.");
                }
              }}
              className="py-3 px-6 bg-green-700 hover:bg-green-800 text-white rounded-lg font-semibold shadow flex items-center gap-2 mx-auto"
            >
              <FileText />
              Download Full Report
            </button>
          </div>
        )}
      </section>

      {/* PROJECT MODAL */}
      {openProjectModal && (
        <Modal onClose={() => setOpenProjectModal(false)}>
          {/*   <CreateProject setOpenProjectModal={setOpenProjectModal} setOpenSubmissionModal={setOpenSubmissionModal} />*/}
          <h2 className="text-2xl font-bold text-green-700 mb-4">
            Create Project
          </h2>

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
        </Modal>
      )}

      {/* SUBMISSION MODAL */}
      {openSubmissionModal && (
        <Modal onClose={() => setOpenSubmissionModal(false)}>
          <h2 className="text-2xl font-bold text-green-700 mb-4 capitalize">
            Submit {currentStage.replace("_", " ")}
          </h2>

          <form
            onSubmit={submitMilestone}
            className="space-y-4"
          >
            <FileUpload
              file={file}
              onFileSelect={(file) => setFile(file)}
              label={`Upload ${currentStage.replace("_", " ")} (PDF)`}
            />

            <button
              disabled={loading}
              className="w-full bg-green-700 text-white py-2 rounded-md disabled:opacity-60"
            >
              {loading
                ? "Submitting..."
                : `Submit ${currentStage.replace("_", " ")}`}
            </button>
          </form>
        </Modal>
      )}
    </>
  );
};

export default CreateSubmissions;

/* Modal Wrapper */

const Modal: React.FC<{ onClose: () => void; children: React.ReactNode }> = ({
  onClose,
  children,
}) => (
  <div
    className="fixed inset-0 bg-black/30 z-50 flex items-center justify-center p-4"
    onClick={onClose}
  >
    <div
      onClick={(e) => e.stopPropagation()}
      className="bg-white rounded-xl w-full max-w-lg p-6 shadow-lg"
    >
      {children}
    </div>
  </div>
);
