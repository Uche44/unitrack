/* eslint-disable @typescript-eslint/no-explicit-any */
import React from "react";
import { useForm } from "react-hook-form";
import type { SubmitHandler, FieldErrors } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import * as z from "zod";
import {
  User,
  Mail,
  Lock,
  GraduationCap,
  ArrowRight,
  Info,
  CheckCircle,
  // Phone,
  Briefcase,
} from "lucide-react";
import { Link } from "react-router-dom";
import api from "../lib/api";

const supervisorSchema = z.object({
  fullName: z.string().min(3, "Full name must be at least 3 characters."),
  staffId: z
    .string()
    .min(4, "Staff ID must be at least 4 characters.")
    .regex(/^[a-zA-Z0-9]+$/, "Staff ID must be alphanumeric."),
  email: z.string().email("Invalid email address."),
  // phoneNumber: z
  //   .string()
  //   .regex(/^0\d{10}$/, "Phone number must be 11 digits (e.g., 09035609172)."),
  department: z.literal("Computer Science"),
  password: z
    .string()
    .min(8, "Password must be at least 8 characters.")
    .regex(/[a-z]/, "Password must contain a lowercase letter."),
  // .regex(/[A-Z]/, "Password must contain an uppercase letter.")
  // .regex(/[0-9]/, "Password must contain a number."),
  role: z.literal("supervisor"),
});

type SupervisorFormInputs = z.infer<typeof supervisorSchema>;

interface FormFieldProps {
  label: string;

  name: keyof SupervisorFormInputs;
  type?: "text" | "email" | "password" | "select" | "tel";
  icon: React.ElementType;
  placeholder?: string;
  options?: string[];

  register: ReturnType<typeof useForm<SupervisorFormInputs>>["register"];
  error: FieldErrors<SupervisorFormInputs> | undefined;
  disabled?: boolean;
}

const FormField: React.FC<FormFieldProps> = ({
  label,
  name,
  type = "text",
  icon: Icon,
  placeholder,
  options,
  register,
  error,
  disabled,
}) => {
  const isSelect = type === "select";

  const errorMessage = error?.[name]?.message?.toString();
  const hasError = !!errorMessage;

  return (
    <div className="mb-5">
      <label
        htmlFor={name as string}
        className="block text-sm font-semibold text-gray-700 mb-1"
      >
        {label}
      </label>
      <div className="relative">
        <Icon className="absolute left-3 top-1/2 transform -translate-y-1/2 text-green-600 w-5 h-5" />

        {isSelect ? (
          <select
            id={name as string}
            {...register(name)}
            disabled={disabled}
            className={`
              w-full pl-10 pr-4 py-2 border rounded-lg bg-white text-gray-800 shadow-sm transition-all
              focus:ring-2 focus:ring-green-500 focus:border-green-500
              ${hasError ? "border-red-500" : "border-gray-300"}
              ${disabled ? "bg-gray-100 cursor-not-allowed" : ""}
            `}
          >
            {options?.map((option) => (
              <option
                key={option}
                value={option}
              >
                {option}
              </option>
            ))}
          </select>
        ) : (
          <input
            id={name as string}
            type={type}
            placeholder={placeholder}
            {...register(name)}
            disabled={disabled}
            className={`
              w-full pl-10 pr-4 py-2 border rounded-lg bg-white text-gray-800 shadow-sm transition-all
              focus:ring-2 focus:ring-green-500 focus:border-green-500
              ${hasError ? "border-red-500" : "border-gray-300"}
              ${disabled ? "bg-gray-100 cursor-not-allowed" : ""}
            `}
          />
        )}
      </div>
      {hasError && (
        <p className="mt-2 text-sm text-red-600 flex items-center">
          <Info className="w-4 h-4 mr-1" /> {errorMessage}
        </p>
      )}
    </div>
  );
};

const SupervisorForm: React.FC = () => {
  const role = "supervisor";
  const department = "Computer Science";

  const {
    register,
    handleSubmit,
    reset,
    formState: { errors, isSubmitting, isSubmitSuccessful },
  } = useForm<SupervisorFormInputs>({
    resolver: zodResolver(supervisorSchema),
    defaultValues: {
      department: department,
      role: role,
    },
  });

  const onSubmit: SubmitHandler<SupervisorFormInputs> = async (data) => {
    try {
      console.log("Submitting:", data);

      const payload = {
        full_name: data.fullName,
        email: data.email,
        role: data.role,
        department: data.department,
        staff_id: data.staffId,

        password: data.password,
      };

      const res = await api.post("/api/signup/", payload);

      if (res.status === 201) {
        console.log("Signup successful:", res.data);
        reset({ department: "Computer Science", role: "supervisor" });
      } else {
        console.error("Unexpected response:", res);
      }
    } catch (error: any) {
      if (error.response) {
        console.error("Signup failed:", error.response.data);
        alert(error.response.data.error || "Signup failed. Please try again.");
      } else {
        console.error("Error:", error);
        alert("Network error. Please check your connection.");
      }
      throw error;
    }
  };

  return (
    <div className="min-h-screen bg-white flex items-center justify-center p-4">
      <div className="w-full max-w-lg bg-white border border-green-100 shadow-xl rounded-2xl p-8 sm:p-10">
        {/* Header */}
        <header className="mb-8 text-center">
          <h1 className="text-3xl font-bold text-green-700 mb-2">
            Create UniTrack Account
          </h1>
          <p className="text-gray-500">
            Register as a Supervisor to oversee and manage projects.
          </p>
        </header>

        {/* Success message */}
        {isSubmitSuccessful && (
          <div className="bg-green-100 border-l-4 border-green-600 text-green-800 p-4 mb-6 rounded-lg shadow-sm flex items-start">
            <CheckCircle className="w-5 h-5 mt-0.5 mr-2" />
            <div>
              <p className="font-semibold">Registration Successful!</p>
              <p className="text-sm">
                Your supervisor account has been created.
              </p>
            </div>
          </div>
        )}

        {/* Form */}
        <form
          onSubmit={handleSubmit(onSubmit)}
          className="space-y-4"
        >
          <FormField
            label="Full Name"
            name="fullName"
            icon={User}
            placeholder="Enter your full name"
            register={register}
            error={errors}
          />

          <FormField
            label="Staff ID"
            name="staffId"
            icon={Briefcase}
            placeholder="Enter your staff identification number"
            register={register}
            error={errors}
          />

          <FormField
            label="Email"
            name="email"
            type="email"
            icon={Mail}
            placeholder="e.g. your.email@university.edu"
            register={register}
            error={errors}
          />

          {/* Phone Number */}
          {/* <FormField
            label="Phone Number"
            name="phoneNumber"
            type="tel"
            icon={Phone}
            placeholder="e.g. 09035609172"
            register={register}
            error={errors}
          /> */}

          <FormField
            label="Password"
            name="password"
            type="password"
            icon={Lock}
            placeholder="Enter a strong password"
            register={register}
            error={errors}
          />

          <FormField
            label="Department"
            name="department"
            type="select"
            icon={GraduationCap}
            options={[department]}
            register={register}
            error={errors}
            disabled
          />

          <input
            type="hidden"
            {...register("role")}
            value={role}
          />

          <button
            type="submit"
            disabled={isSubmitting}
            className={`w-full flex items-center justify-center px-4 py-3 text-base font-semibold rounded-lg text-white shadow-md transition-all transform ${
              isSubmitting
                ? "bg-green-400 cursor-not-allowed"
                : "bg-green-600 hover:bg-green-700 hover:scale-[1.02] active:scale-[0.98] focus:ring-4 focus:ring-green-300"
            }`}
          >
            {isSubmitting ? (
              <>
                <svg
                  className="animate-spin -ml-1 mr-3 h-5 w-5 text-white"
                  xmlns="http://www.w3.org/2000/svg"
                  fill="none"
                  viewBox="0 0 24 24"
                >
                  <circle
                    className="opacity-25"
                    cx="12"
                    cy="12"
                    r="10"
                    stroke="currentColor"
                    strokeWidth="4"
                  />
                  <path
                    className="opacity-75"
                    fill="currentColor"
                    d="M4 12a8 8 0 018-8V0C5.37 0 0 5.37 0 12h4z"
                  />
                </svg>
                Signing up...
              </>
            ) : (
              <>
                Sign up as Supervisor <ArrowRight className="w-5 h-5 ml-2" />
              </>
            )}
          </button>
        </form>

        <footer className="mt-8 text-center text-xs text-gray-500 leading-relaxed">
          Already have an account?{" "}
          <span className="text-green-600 font-medium">
            <Link to="/auth/login">Login</Link>
          </span>{" "}
        </footer>
      </div>
    </div>
  );
};

export default SupervisorForm;
