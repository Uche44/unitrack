export type UserRole = "student" | "supervisor" | "admin";

export interface User {
  id: number;
  fullname: string;
  email: string;
  role: UserRole;
  staffId?: string;
  matricNo?: string;
}

export interface Supervisor {
  id: number;
  fullName: string;
  email: string;
  staffId?: string;
}

export interface Student {
  id: number;
  fullName: string;
  email: string;
  matricNo: string;
  supervisor?: Supervisor;
}
