import React, { createContext, useState, useEffect } from "react";

interface AuthContextType {
  token: string | null;
  userId: number | null;
  username: string | null;
  login: (token: string, userId: number, username: string) => void;
  logout: () => void;
  isAuthenticated: boolean;
}

export const AuthContext = createContext<AuthContextType | undefined>(
  undefined
);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  // Server & initial client render: no token (prevents hydration mismatch)
  const [token, setToken] = useState<string | null>(null);
  const [userId, setUserId] = useState<number | null>(null);
  const [username, setUsername] = useState<string | null>(null);
  const [isMounted, setIsMounted] = useState(false);

  // Load auth from localStorage after hydration completes
  useEffect(() => {
    const savedToken = localStorage.getItem("auth_token");
    const savedUserId = localStorage.getItem("auth_user_id");
    const savedUsername = localStorage.getItem("auth_username");

    if (savedToken && savedUserId) {
      setToken(savedToken);
      setUserId(parseInt(savedUserId));
      setUsername(savedUsername);
    }
    setIsMounted(true);
  }, []);

  const login = (newToken: string, newUserId: number, newUsername: string) => {
    setToken(newToken);
    setUserId(newUserId);
    setUsername(newUsername);

    localStorage.setItem("auth_token", newToken);
    localStorage.setItem("auth_user_id", newUserId.toString());
    localStorage.setItem("auth_username", newUsername);
  };

  const logout = () => {
    setToken(null);
    setUserId(null);
    setUsername(null);

    localStorage.removeItem("auth_token");
    localStorage.removeItem("auth_user_id");
    localStorage.removeItem("auth_username");
  };

  return (
    <AuthContext.Provider
      value={{
        token,
        userId,
        username,
        login,
        logout,
        isAuthenticated: !!token,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = React.useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth must be used within AuthProvider");
  }
  return context;
}
