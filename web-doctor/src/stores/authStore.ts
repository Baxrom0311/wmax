import { create } from "zustand";
import type { TokenPair } from "../lib/types";

interface AuthState {
  token: string | null;
  user: TokenPair | null;
  isAuthenticated: boolean;
  setAuth: (pair: TokenPair) => void;
  logout: () => void;
}

const TOKEN_KEY = "nazorat_doctor_jwt";
const USER_KEY = "nazorat_doctor_user";

function loadInitialState() {
  const token = localStorage.getItem(TOKEN_KEY);
  const userJson = localStorage.getItem(USER_KEY);
  let user: TokenPair | null = null;
  if (userJson) {
    try {
      user = JSON.parse(userJson);
    } catch {
      user = null;
    }
  }
  return {
    token,
    user,
    isAuthenticated: Boolean(token),
  };
}

export const useAuthStore = create<AuthState>((set) => ({
  ...loadInitialState(),
  setAuth: (pair: TokenPair) => {
    localStorage.setItem(TOKEN_KEY, pair.access_token);
    localStorage.setItem(USER_KEY, JSON.stringify(pair));
    set({
      token: pair.access_token,
      user: pair,
      isAuthenticated: true,
    });
  },
  logout: () => {
    localStorage.removeItem(TOKEN_KEY);
    localStorage.removeItem(USER_KEY);
    set({
      token: null,
      user: null,
      isAuthenticated: false,
    });
  },
}));
