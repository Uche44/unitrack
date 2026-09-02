/* eslint-disable @typescript-eslint/no-explicit-any */
import React from "react";
import { useForm } from "react-hook-form";
import type { SubmitHandler, FieldErrors, Path } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import * as z from "zod";
import { Mail, Lock, ArrowRight, Info, CheckCircle } from "lucide-react";
import api from "../lib/api";
import { useNavigate } from "react-router-dom";
import { useUserStore } from "../context/user-context";
import { Link } from "react-router-dom";

const loginSchema = z.object({
  email: z.string().email("Invalid email address."),
  password: z
    .string()
    .min(8, "Password must be at least 8 characters.")
    .regex(/[a-z]/, "Password must contain a lowercase letter."),
});

type LoginFormInputs = z.infer<typeof loginSchema>;

interface FormFieldProps {
  label: string;

  name: Path<LoginFormInputs>;
  type?: "email" | "password" | "text" | "select";
  icon: React.ElementType;
  placeholder?: string;
  options?: string[];

  register: ReturnType<typeof useForm<LoginFormInputs>>["register"];
  error: FieldErrors<LoginFormInputs> | undefined;
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
        htmlFor={name}
        className="block text-sm font-semibold text-gray-700 mb-1"
      >
        {label}
      </label>
      <div className="relative">
        <Icon className="absolute left-3 top-1/2 transform -translate-y-1/2 text-green-600 w-5 h-5" />

        {isSelect ? (
          <select
            id={name}
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
            id={name}
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

const LoginForm: React.FC = () => {
  const {
    register,
    handleSubmit,
    reset,
    formState: { errors, isSubmitting, isSubmitSuccessful },
  } = useForm<LoginFormInputs>({
    resolver: zodResolver(loginSchema),
  });

  const navigate = useNavigate();
  const setUser = useUserStore((state) => state.setUser);
  // const [showGuestSelector, setShowGuestSelector] = useState(false);

  const onSubmit: SubmitHandler<LoginFormInputs> = async (data) => {
    try {
      console.log("Submitting:", data);

      const payload = {
        email: data.email,
        password: data.password,
      };

      const res = await api.post("/api/login/", payload);

      if (res.status === 200) {
        console.log("login successful:", res.data);

        // Save tokens in localStorage if they are returned in the response body
        if (res.data.access) {
          localStorage.setItem("access_token", res.data.access);
        }
        if (res.data.refresh) {
          localStorage.setItem("refresh_token", res.data.refresh);
        }

        const userRole = res.data.user?.role;

        // localStorage.setItem("userRole", userRole);

        // Navigate based on role
        if (userRole === "admin") {
          setUser({
            id: res.data.user?.id,
            fullname: res.data.user?.full_name,
            email: res.data.user?.email,
            role: userRole,
            staffId: res.data.user?.staff_id,
          });
          navigate("/admin-dashboard");
        } else if (userRole === "supervisor") {
          setUser({
            id: res.data.user?.id,
            fullname: res.data.user?.full_name,
            email: res.data.user?.email,
            role: userRole,
            staffId: res.data.user?.staff_id,
          });
          navigate("/supervisor-dashboard");
        } else if (userRole === "student") {
          setUser({
            id: res.data.user?.id,
            fullname: res.data.user?.full_name,
            email: res.data.user?.email,
            role: userRole,
            matricNo: res.data.user?.matric_no,
          });

          navigate("/student-dashboard");
        } else {
          alert("Unknown role. Please contact support.");
        }

        reset({ email: "", password: "" });
      } else {
        console.error("Unexpected response:", res);
      }
    } catch (error: any) {
      if (error.response) {
        console.error("Login failed:", error.response.data);
        alert(error.response.data.error || "Login failed. Please try again.");
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
            Log in to your Account
          </h1>
          <p className="text-gray-500">
            Start managing your school projects with ease.
          </p>
        </header>

        {/* Success message */}
        {isSubmitSuccessful && (
          <div className="bg-green-100 border-l-4 border-green-600 text-green-800 p-4 mb-6 rounded-lg shadow-sm flex items-start">
            <CheckCircle className="w-5 h-5 mt-0.5 mr-2" />
            <div>
              <p className="font-semibold">Login Successful!</p>
              <p className="text-sm">Redirecting to your dashboard...</p>
            </div>
          </div>
        )}

        {/* Form */}
        <form
          onSubmit={handleSubmit(onSubmit)}
          className="space-y-4"
        >
          {/* Email */}
          <FormField
            label="Email"
            name="email"
            type="email"
            icon={Mail}
            placeholder="e.g. your.email@university.edu"
            register={register}
            error={errors}
          />

          {/* Password */}
          <FormField
            label="Password"
            name="password"
            type="password"
            icon={Lock}
            placeholder="Enter a strong password"
            register={register}
            error={errors}
          />

          {/* Submit Button */}
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
                Logging in...
              </>
            ) : (
              <>
                Log in
                <ArrowRight className="w-5 h-5 ml-2" />
              </>
            )}
          </button>
        </form>

        {/* Guest Login Button */}
        {/* <button
          onClick={() => setShowGuestSelector(true)}
          className="w-full mt-4 px-4 py-3 text-base font-semibold rounded-lg text-green-700 bg-green-50 border-2 border-green-600 hover:bg-green-100 transition-all"
        >
          Continue as Guest
        </button> */}

        {/* Footer */}
        <footer className="mt-8 text-center text-xs text-gray-500 leading-relaxed">
          Go to <Link to="/">home</Link>
        </footer>
      </div>
    </div>
  );
};

export default LoginForm;
