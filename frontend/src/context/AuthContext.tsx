import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useState,
  type ReactNode,
} from "react";

import { getCurrentUser, login as loginRequest, register as registerRequest } from "../api/auth";
import { ACCESS_TOKEN_STORAGE_KEY } from "../api/client";
import type { User } from "../types/auth";

interface AuthContextValue {
  user: User | null;
  isLoading: boolean;
  error: string | null;
  login: (email: string, password: string) => Promise<void>;
  register: (
    email: string,
    password: string,
    fullName: string,
  ) => Promise<void>;
  logout: () => void;
}

const AuthContext = createContext<AuthContextValue | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const logout = useCallback(() => {
    window.localStorage.removeItem(ACCESS_TOKEN_STORAGE_KEY);
    setUser(null);
  }, []);

  useEffect(() => {
    const token = window.localStorage.getItem(ACCESS_TOKEN_STORAGE_KEY);

    if (!token) {
      setIsLoading(false);
      return;
    }

    getCurrentUser()
      .then(setUser)
      .catch(() => {
        window.localStorage.removeItem(ACCESS_TOKEN_STORAGE_KEY);
      })
      .finally(() => setIsLoading(false));
  }, []);

  useEffect(() => {
    const handleUnauthorized = () => setUser(null);

    window.addEventListener("auth:unauthorized", handleUnauthorized);

    return () =>
      window.removeEventListener("auth:unauthorized", handleUnauthorized);
  }, []);

  const login = useCallback(async (email: string, password: string) => {
    setError(null);

    try {
      const token = await loginRequest(email, password);
      window.localStorage.setItem(ACCESS_TOKEN_STORAGE_KEY, token.access_token);

      const currentUser = await getCurrentUser();
      setUser(currentUser);
    } catch {
      setError("Incorrect email or password.");
      throw new Error("login_failed");
    }
  }, []);

  const register = useCallback(
    async (email: string, password: string, fullName: string) => {
      setError(null);

      try {
        await registerRequest({
          email,
          password,
          full_name: fullName || null,
        });

        await login(email, password);
      } catch (registerError) {
        if ((registerError as Error).message === "login_failed") {
          throw registerError;
        }

        setError("Unable to create an account with this email.");
        throw new Error("register_failed");
      }
    },
    [login],
  );

  return (
    <AuthContext.Provider
      value={{ user, isLoading, error, login, register, logout }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth(): AuthContextValue {
  const context = useContext(AuthContext);

  if (!context) {
    throw new Error("useAuth must be used within an AuthProvider");
  }

  return context;
}
