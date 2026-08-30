/* eslint-disable @typescript-eslint/no-explicit-any */
import { useParams } from "react-router-dom";
import { useState, useEffect } from "react";
import api from "../../../lib/api";
import { FileText } from "lucide-react";
import { useUserStore } from "../../../context/user-context";
import { Navigate } from "react-router-dom";
import type { StudentResponse, ProjectDetail } from "../../../types/student";
import { camelize } from "../../../types/camelize";
import toast from "react-hot-toast";
import PdfViewerModal from "../../../components/pdf-viewer-modal";

const DetailRow = ({ label, value }: { label: string; value: string }) => (
  <span className="flex gap-2 w-full">
    <p className="font-semibold text-xl text-green-700">{label}</p>
    <p className="font-normal text-xl text-gray-900">{value}</p>
  </span>
);

const StudentPage = () => {
  const { supervisorId, studentId } = useParams();
  const [student, setStudent] = useState<StudentResponse | null>(null);
  const [project, setProject] = useState<ProjectDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const [showApproveModal, setShowApproveModal] = useState(false);
  const [showRejectModal, setShowRejectModal] = useState(false);
  const [rejectionComment, setRejectionComment] = useState("");
  const [actionLoading, setActionLoading] = useState(false);
  const [selectedSubmissionId, setSelectedSubmissionId] = useState<
    number | null
  >(null);

  const user = useUserStore((state) => state.user);

  useEffect(() => {
    const loadData = async () => {
      try {
        setLoading(true);
        // 1. Fetch Student Details
        const studentRes = await api.get(
          `/api/supervisors/${supervisorId}/students/${studentId}/`,
        );
        setStudent(camelize(studentRes.data));

        // 2. Fetch Project Details
        // We use the new endpoint we created
        try {
          const projectRes = await api.get(
            `/api/supervisor/student/${studentId}/project/`,
          );
          setProject(camelize(projectRes.data));
          console.log("project data:", projectRes.data);
        } catch (err: any) {
          if (err.response && err.response.status === 404) {
            setProject(null); // No project found
          } else {
            console.error("Error fetching project:", err);
          }
        }
      } catch (err) {
        console.error("Failed to load student data:", err);
      } finally {
        setLoading(false);
      }
    };

    loadData();
  }, [supervisorId, studentId]);

  // Protect route - redirect if not supervisor
  if (user?.role !== "supervisor") {
    return (
      <Navigate
        to="/auth/login"
        replace
      />
    );
  }

  const handleApprove = async () => {
    if (!project || !selectedSubmissionId) return;

    setActionLoading(true);
    try {
      await api.post(`/api/submissions/${selectedSubmissionId}/action/`, {
        action: "approve",
      });

      // Refresh project data
      const projectRes = await api.get(
        `/api/supervisor/student/${studentId}/project/`,
      );
      console.log("project data after approval:", projectRes.data);
      setProject(projectRes.data);
      setShowApproveModal(false);
      setSelectedSubmissionId(null);

      // Show success toast
      toast.success("Submission approved successfully!");
    } catch (err: any) {
      console.error("Failed to approve submission:", err);
      alert(err?.response?.data?.error || "Failed to approve submission");
    } finally {
      setActionLoading(false);
    }
  };

  const handleReject = async () => {
    if (!project || !selectedSubmissionId) return;

    setActionLoading(true);
    try {
      await api.post(`/api/submissions/${selectedSubmissionId}/action/`, {
        action: "reject",
        comment: rejectionComment,
      });

      // Refresh project data
      const projectRes = await api.get(
        `/api/supervisor/student/${studentId}/project/`,
      );
      setProject(projectRes.data);
      console.log("project data after rejection:", projectRes.data);
      setShowRejectModal(false);
      setRejectionComment("");
      setSelectedSubmissionId(null);

      // Show success toast
      toast.success("Submission rejected. Student can resubmit.");
    } catch (err: any) {
      console.error("Failed to reject submission:", err);
      alert(err?.response?.data?.error || "Failed to reject submission");
    } finally {
      setActionLoading(false);
    }
  };

  if (loading)
    return <div className="p-8 text-center text-gray-500">Loading...</div>;
  if (!student)
    return (
      <div className="p-8 text-center text-red-500">Student not found</div>
    );

  const details = [
    { label: "Student Name:", value: student.fullName },
    { label: "Student Email:", value: student.email },
    { label: "Matric Number:", value: student.matricNo },
  ];

  return (
    <section className="w-full min-h-screen pt-16 bg-gray-100 p-6 space-y-6">
      {/* Student Details Card */}
      <section className="h-fit w-full bg-white px-6 py-6 rounded-2xl shadow-sm">
        <h2 className="text-3xl font-bold mb-4 border-b pb-2">
          Student Details
        </h2>
        <div className="flex flex-col gap-4 md:flex-row md:justify-between md:items-end">
          <div className="space-y-2">
            {details.map((item, i) => (
              <DetailRow
                key={i}
                label={item.label}
                value={item.value || "N/A"}
              />
            ))}
          </div>
          <span className="flex gap-2 items-center bg-green-50 px-4 py-2 rounded-lg border border-green-100">
            <p className="font-bold text-lg text-green-700">
              Supervisor (You):
            </p>
            <p className="font-semibold text-lg text-gray-900">
              {student.supervisor.fullName}
            </p>
          </span>
        </div>
      </section>

      {/* Project Details Card */}
      <section className="h-fit w-full bg-white px-6 py-6 rounded-2xl shadow-sm">
        <h2 className="text-2xl font-bold mb-4 flex items-center gap-2">
          <FileText className="text-green-600" />
          Project
        </h2>

        {project ? (
          <div className="space-y-6">
            <div className="md:flex md:items-start md:justify-between">
              <div className="h-fit md:w-[70%]">
                <h3 className="md:text-xl font-bold text-gray-800">
                  <span className="font-semibold mb-4">Title:</span>{" "}
                  {project.title || "Untitled Project"}
                </h3>
                <p className="text-gray-600 mt-2">
                  <span className="font-semibold mb-4">Description:</span>{" "}
                  {project.description || "No description provided."}
                </p>
                <div className="mt-2 text-sm text-gray-500">
                  Status:{" "}
                  <span className="font-medium text-green-600 capitalize">
                    {project.status.replace("_", " ")}
                  </span>
                </div>
              </div>

              {/* Approve/Reject Buttons - Generic Logic */}
              {(() => {
                // Find any PENDING submission (not approved, not rejected)
                // We want the LATEST pending one ideally, or just the latest submission if it's pending.
                // Actually, sequential flow says we only care about the latest submission the student made.

                const latestSubmission = [...project.submissions]
                  .sort((a, b) => b.version - a.version) // First sort by version
                  .sort(
                    (a, b) =>
                      new Date(b.submittedAt).getTime() -
                      new Date(a.submittedAt).getTime(),
                  )[0]; // Then by date just in case

                // Show buttons if the latest submission exists and is PENDING
                const showButtons =
                  latestSubmission &&
                  !latestSubmission.isApproved &&
                  !latestSubmission.isRejected;

                return showButtons ? (
                  <div className="mt-4 flex flex-col gap-3 items-end">
                    <p className="text-sm text-gray-500">
                      Action required for{" "}
                      <span className="font-semibold">
                        {latestSubmission.milestone.replace("_", " ")}
                      </span>
                    </p>
                    <div className="flex gap-3">
                      <button
                        onClick={() => {
                          setSelectedSubmissionId(latestSubmission.id);
                          setShowApproveModal(true);
                        }}
                        className="px-3 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors font-medium shadow-sm cursor-pointer"
                      >
                        ✓ Approve
                      </button>
                      <button
                        onClick={() => {
                          setSelectedSubmissionId(latestSubmission.id);
                          setShowRejectModal(true);
                        }}
                        className="px-3 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-colors font-medium shadow-sm cursor-pointer"
                      >
                        ✗ Reject
                      </button>
                    </div>
                  </div>
                ) : project.status === "completed" ? (
                  <div className="mt-4 p-3 bg-green-50 border border-green-200 rounded-lg">
                    <p className="text-green-700 text-sm font-medium">
                      ✓ Project Completed
                    </p>
                  </div>
                ) : null;
              })()}
            </div>

            {/* Submissions Section - Grouped by Milestone */}
            <div className="border-t pt-4 space-y-6">
              {/* 
                    We want to show the current active submission clearly.
                    Then history below.
                 */}
              <h3 className="text-xl font-bold text-gray-800">Submissions</h3>

              {project.submissions.length === 0 ? (
                <p className="text-gray-500 italic">No submissions yet.</p>
              ) : (
                <div className="space-y-4">
                  {/* Simply map all submissions, latest first */}
                  {[...project.submissions]
                    .sort(
                      (a, b) =>
                        new Date(b.submittedAt).getTime() -
                        new Date(a.submittedAt).getTime(),
                    )
                    .map((submission) => (
                      <div
                        key={submission.id}
                        className={`border rounded-lg p-4 ${
                          !submission.isApproved && !submission.isRejected
                            ? "border-blue-300 bg-blue-50"
                            : submission.isApproved
                              ? "border-gray-200 bg-white"
                              : "border-red-200 bg-red-50"
                        }`}
                      >
                        <div className="flex justify-between items-start">
                          <div>
                            <div className="flex items-center gap-2">
                              <h4 className="font-bold text-lg capitalize">
                                {submission.milestone.replace("_", " ")}
                              </h4>
                              <span className="text-xs bg-gray-200 text-gray-700 px-2 py-0.5 rounded-full">
                                v{submission.version}
                              </span>
                            </div>
                            <p className="text-sm text-gray-500">
                              {new Date(
                                submission.submittedAt,
                              ).toLocaleString()}
                            </p>

                            {/* Status Badge */}
                            <div className="mt-2">
                              {submission.isApproved && (
                                <span className="text-green-600 font-medium text-sm">
                                  ✓ Approved
                                </span>
                              )}
                              {submission.isRejected && (
                                <span className="text-red-600 font-medium text-sm">
                                  ✗ Rejected
                                </span>
                              )}
                              {!submission.isApproved &&
                                !submission.isRejected && (
                                  <span className="text-yellow-600 font-medium text-sm">
                                    ⏳ Pending Review
                                  </span>
                                )}
                            </div>

                            {/* Rejection Comment */}
                            {submission.isRejected &&
                              submission.rejectionComment && (
                                <div className="mt-2 text-sm text-red-700 bg-red-100 p-2 rounded">
                                  <strong>Feedback:</strong>{" "}
                                  {submission.rejectionComment}
                                </div>
                              )}
                          </div>

                          <button
                            onClick={() => setPreviewUrl(submission.fileUrl)}
                            className="px-4 py-2 bg-white border border-gray-300 text-gray-700 rounded hover:bg-gray-50 text-sm font-medium"
                          >
                            View Document
                          </button>
                        </div>
                      </div>
                    ))}
                </div>
              )}
            </div>
          </div>
        ) : (
          <div className="text-center py-10 bg-gray-50 rounded-lg border border-dashed border-gray-300">
            <p className="text-gray-500 text-lg">
              This student has not started a project yet.
            </p>
          </div>
        )}
      </section>

      {/* File Preview Modal */}
      <PdfViewerModal
        isOpen={!!previewUrl}
        onClose={() => setPreviewUrl(null)}
        pdfUrl={previewUrl || ""}
        title={`${student?.fullName}'s submission`}
        showCorrectionsLink={true}
      />

      {/* Approve Confirmation Modal */}
      {showApproveModal && (
        <div className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4">
          <div className="bg-white rounded-lg w-full max-w-md p-6 shadow-2xl">
            <h3 className="font-bold text-xl mb-4 text-green-700">
              Approve Submission
            </h3>
            <p className="text-gray-600 mb-6">
              Are you sure you want to approve this submission? The student will
              be able to proceed to the next stage.
            </p>
            <div className="flex gap-3 justify-end">
              <button
                onClick={() => {
                  setShowApproveModal(false);
                  setSelectedSubmissionId(null);
                }}
                disabled={actionLoading}
                className="px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors disabled:opacity-50"
              >
                Cancel
              </button>
              <button
                onClick={handleApprove}
                disabled={actionLoading}
                className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors disabled:opacity-50"
              >
                {actionLoading ? "Approving..." : "Approve"}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Reject Modal with Comment */}
      {showRejectModal && (
        <div className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4">
          <div className="bg-white rounded-lg w-full max-w-md p-6 shadow-2xl">
            <h3 className="font-bold text-xl mb-4 text-red-700">
              Reject Submission
            </h3>
            <p className="text-gray-600 mb-4">
              Please provide feedback to help the student improve their
              submission.
            </p>
            <textarea
              value={rejectionComment}
              onChange={(e) => setRejectionComment(e.target.value)}
              placeholder="Enter your feedback here..."
              className="w-full border border-gray-300 rounded-lg p-3 mb-4 min-h-[120px] focus:outline-none focus:ring-2 focus:ring-red-500"
            />
            <div className="flex gap-3 justify-end">
              <button
                onClick={() => {
                  setShowRejectModal(false);
                  setRejectionComment("");
                  setSelectedSubmissionId(null);
                }}
                disabled={actionLoading}
                className="px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors disabled:opacity-50"
              >
                Cancel
              </button>
              <button
                onClick={handleReject}
                disabled={actionLoading}
                className="px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-colors disabled:opacity-50"
              >
                {actionLoading ? "Rejecting..." : "Reject"}
              </button>
            </div>
          </div>
        </div>
      )}
    </section>
  );
};

export default StudentPage;
