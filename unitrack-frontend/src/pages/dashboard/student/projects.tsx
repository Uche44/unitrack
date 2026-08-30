import React, { useEffect, useState } from "react";
import api from "../../../lib/api";
import type { Submission } from "../../../types/student";
import { camelize } from "../../../types/camelize";
import PdfViewerModal from "../../../components/pdf-viewer-modal";

interface Project {
  id: number;
  title: string;
  description: string;
  status: string;
  is_approved: boolean;
  student: number;
  supervisor: number;
  created_at: string;
}

const ProjectDashboard: React.FC = () => {
  const [projects, setProjects] = useState<Project[]>([]);
  const [submissions, setSubmissions] = useState<Submission[]>([]);
  const [loading, setLoading] = useState(true);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);

  useEffect(() => {
    const fetchData = async () => {
      try {
        // Projects for logged-in student
        const projectRes = await api.get("/api/projects/");
        setProjects(projectRes.data);

        // Submissions for logged-in student
        const submissionRes = await api.get("/api/submissions/");
        setSubmissions(camelize(submissionRes.data));
      } catch (err) {
        console.error("Failed to fetch data:", err);
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, []);

  if (loading) return <p>Loading...</p>;

  if (projects.length === 0) {
    return (
      <div className="max-w-5xl mx-auto pt-20 text-center">
        <p className="text-gray-600 text-lg">
          You haven’t submitted any projects yet.
        </p>
      </div>
    );
  }

  return (
    <div className="max-w-5xl mx-auto pt-20 relative flex flex-col-reverse">
      {projects.map((project) => {
        // Get latest proposal submission for this project
        const latestProposal = submissions
          .filter((s) => s.project === project.id && s.milestone === "proposal")
          .sort((a, b) => b.version - a.version)[0];

        return (
          <div
            key={project.id}
            className="bg-white rounded-lg shadow p-6 border border-green-500 mb-6"
          >
            <h2 className="text-2xl font-bold text-green-700">
              {project.title}
            </h2>
            <p className="text-gray-700 mt-2">{project.description}</p>

            {/* Status Badges */}
            <div className="mt-3 flex gap-2 flex-wrap">
              {project.status === "proposal_pending" &&
                !latestProposal?.isRejected && (
                  <span className="inline-block px-3 py-1 text-sm text-white bg-yellow-500 rounded-full">
                    ⏳ Awaiting Approval
                  </span>
                )}

              {project.status === "proposal_approved" && (
                <span className="inline-block px-3 py-1 text-sm text-white bg-green-600 rounded-full">
                  ✓ Proposal Approved
                </span>
              )}

              {latestProposal?.isRejected && (
                <span className="inline-block px-3 py-1 text-sm text-white bg-red-600 rounded-full">
                  ✗ Proposal Rejected
                </span>
              )}
            </div>

            {/* Rejection Message */}
            {latestProposal?.isRejected && (
              <div className="mt-4 p-4 bg-red-50 border border-red-200 rounded-lg">
                <div className="flex items-start gap-2">
                  <span className="text-red-600 text-2xl">✗</span>
                  <div className="flex-1">
                    <p className="font-semibold text-red-800 mb-1">
                      Your proposal was rejected. Submit another proposal.
                    </p>
                    {latestProposal.rejectionComment && (
                      <div className="mt-2">
                        <p className="text-sm font-medium text-red-700">
                          Supervisor Feedback:
                        </p>
                        <p className="text-sm text-red-600 mt-1 italic">
                          "{latestProposal.rejectionComment}"
                        </p>
                      </div>
                    )}
                  </div>
                </div>
              </div>
            )}

            {/* Submissions for this project */}
            <div className="mt-4 space-y-3">
              <h3 className="font-semibold text-lg border-b pb-1">
                Submissions
              </h3>
              {submissions
                .filter((s) => s.project === project.id)
                .map((submission) => (
                  <div
                    key={submission.id}
                    className={`p-3 border rounded-md ${
                      submission.isRejected
                        ? "border-red-300 bg-red-50"
                        : submission.isApproved
                          ? "border-green-300 bg-green-50"
                          : "border-gray-200 bg-gray-50"
                    }`}
                  >
                    <div className="flex justify-between items-center">
                      <div>
                        <span className="text-sm font-semibold text-gray-600 capitalize block">
                          {submission.milestone.replace("_", " ")} (v
                          {submission.version})
                        </span>
                        <span className="text-xs text-gray-400">
                          {new Date(submission.submittedAt).toLocaleString()}
                        </span>
                        {submission.isApproved && (
                          <span className="ml-2 text-xs text-green-600 font-medium">
                            ✓ Approved
                          </span>
                        )}
                        {submission.isRejected && (
                          <span className="ml-2 text-xs text-red-600 font-medium">
                            ✗ Rejected
                          </span>
                        )}
                      </div>
                      <button
                        onClick={() => setPreviewUrl(submission.fileUrl)}
                        className="text-white bg-green-600 hover:bg-green-700 px-3 py-1 rounded-md text-sm transition-colors"
                      >
                        View Document
                      </button>
                    </div>
                  </div>
                ))}
              {submissions.filter((s) => s.project === project.id).length ===
                0 && (
                <p className="text-gray-500 italic text-sm">
                  No files submitted yet.
                </p>
              )}
            </div>
          </div>
        );
      })}

      {/* File Preview Modal */}
      <PdfViewerModal
        isOpen={!!previewUrl}
        onClose={() => setPreviewUrl(null)}
        pdfUrl={previewUrl || ""}
        title="Document Preview"
        showCorrectionsLink={false}
      />
    </div>
  );
};

export default ProjectDashboard;
