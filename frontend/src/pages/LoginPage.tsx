import { useState, type FormEvent } from "react";
import { Navigate, useLocation, useNavigate } from "react-router-dom";

import { useAuth } from "../context/AuthContext";

type Mode = "login" | "register";

export function LoginPage() {
  const { user, error, login, register } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();

  const [mode, setMode] = useState<Mode>("login");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [fullName, setFullName] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);

  if (user) {
    const redirectTo =
      (location.state as { from?: string } | null)?.from ?? "/dashboard";

    return <Navigate to={redirectTo} replace />;
  }

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();

    if (!email.trim() || !password) {
      return;
    }

    setIsSubmitting(true);

    try {
      if (mode === "login") {
        await login(email.trim(), password);
      } else {
        await register(email.trim(), password, fullName.trim());
      }

      navigate("/dashboard", { replace: true });
    } catch {
      // error message is surfaced via useAuth().error
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="page">
      <div className="card auth-card">
        <span className="eyebrow">AI Enterprise Knowledge Platform</span>
        <h1>{mode === "login" ? "Sign in" : "Create your account"}</h1>
        <p>
          {mode === "login"
            ? "Sign in to access your workspaces."
            : "Register to start building a workspace."}
        </p>

        <form className="auth-form" onSubmit={handleSubmit}>
          {mode === "register" && (
            <label className="auth-form__field">
              Full name
              <input
                type="text"
                value={fullName}
                onChange={(event) => setFullName(event.target.value)}
                placeholder="Jane Doe"
                autoComplete="name"
              />
            </label>
          )}

          <label className="auth-form__field">
            Email
            <input
              type="email"
              required
              value={email}
              onChange={(event) => setEmail(event.target.value)}
              placeholder="you@company.com"
              autoComplete="email"
            />
          </label>

          <label className="auth-form__field">
            Password
            <input
              type="password"
              required
              minLength={8}
              value={password}
              onChange={(event) => setPassword(event.target.value)}
              placeholder="********"
              autoComplete={
                mode === "login" ? "current-password" : "new-password"
              }
            />
          </label>

          {error && (
            <p className="status error" role="alert">
              {error}
            </p>
          )}

          <button type="submit" disabled={isSubmitting}>
            {isSubmitting
              ? "Please wait..."
              : mode === "login"
                ? "Sign in"
                : "Create account"}
          </button>
        </form>

        <button
          type="button"
          className="auth-card__toggle"
          onClick={() => setMode(mode === "login" ? "register" : "login")}
        >
          {mode === "login"
            ? "Need an account? Register"
            : "Already have an account? Sign in"}
        </button>
      </div>
    </div>
  );
}
