export interface StudentResponse {
  id: number;
  fullName: string;
  email: string;
  matricNo: string;
  department: string;
  role: string;
  createdAt: string;
  supervisor: {
    id: number;
    fullName: string;
    email?: string;
    staffId?: string;
    isApproved?: boolean;
    isFullyBooked?: boolean;
  };
}

export interface Submission {
  id: number;
  milestone: string;
  fileUrl: string;
  version: number;
  submittedAt: string;
  isRead?: boolean;
  isApproved?: boolean;
  isRejected?: boolean;
  rejectionComment?: string;
  comment?: string;
  project: number;
}

export interface ProjectDetail {
  id: number;
  title: string;
  description: string;
  status: string;
  createdAt: string;
  submissions: Submission[];
}
