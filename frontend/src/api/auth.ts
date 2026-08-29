import { apiClient } from "./client";
import type { RegisterRequest, TokenResponse, User } from "../types/auth";

export async function login(
  email: string,
  password: string,
): Promise<TokenResponse> {
  const body = new URLSearchParams();
  body.set("username", email);
  body.set("password", password);

  const response = await apiClient.post<TokenResponse>(
    "/auth/login",
    body,
    {
      headers: {
        "Content-Type": "application/x-www-form-urlencoded",
      },
    },
  );

  return response.data;
}

export async function register(
  payload: RegisterRequest,
): Promise<User> {
  const response = await apiClient.post<User>("/auth/register", payload);

  return response.data;
}

export async function getCurrentUser(): Promise<User> {
  const response = await apiClient.get<User>("/auth/me");

  return response.data;
}
