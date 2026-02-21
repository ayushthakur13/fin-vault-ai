import React, { useState } from "react";
import { LogIn, UserPlus } from "lucide-react";
import { useAuth } from "@/lib/AuthContext";

interface LoginPageProps {
  apiUrl: string;
}

export default function LoginPage({ apiUrl }: LoginPageProps) {
  const { login } = useAuth();
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [isSignup, setIsSignup] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setLoading(true);

    try {
      const endpoint = isSignup
        ? `${apiUrl}/api/auth/signup`
        : `${apiUrl}/api/auth/login`;

      const response = await fetch(endpoint, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ username, password }),
      });

      if (!response.ok) {
        const data = await response.json();
        throw new Error(data.detail || "Authentication failed");
      }

      const data = await response.json();
      
      // Update auth context and redirect
      login(data.access_token, data.user_id, data.username);
      
      // If signup, clear form and show login message
      if (isSignup) {
        setUsername("");
        setPassword("");
        setIsSignup(false);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Authentication failed");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-linear-to-br from-blue-50 to-indigo-100 flex items-center justify-center p-4">
      <div className="bg-white rounded-lg shadow-xl p-8 w-full max-w-md">
        <div className="text-center mb-8">
          <h1 className="text-3xl font-bold text-gray-900">FinVault AI</h1>
          <p className="text-gray-600 mt-2">Financial Research Agent</p>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Username
            </label>
            <input
              type="text"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              placeholder="Enter username"
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              required
              minLength={3}
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Password
            </label>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="Enter password (min 6 chars)"
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              required
              minLength={6}
              maxLength={128}
              title="Password must be 6-128 characters"
            />
          </div>

          {error && (
            <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg">
              {error}
            </div>
          )}

          <button
            type="submit"
            disabled={loading}
            className="w-full bg-blue-600 hover:bg-blue-700 disabled:bg-gray-400 text-white font-semibold py-2 px-4 rounded-lg flex items-center justify-center gap-2 transition"
          >
            {isSignup ? (
              <>
                <UserPlus size={20} />
                Create Account
              </>
            ) : (
              <>
                <LogIn size={20} />
                Sign In
              </>
            )}
          </button>
        </form>

        <div className="mt-6 text-center">
          <p className="text-gray-600">
            {isSignup
              ? "Already have an account?"
              : "Don't have an account?"}
            {" "}
            <button
              onClick={() => setIsSignup(!isSignup)}
              className="text-blue-600 hover:text-blue-700 font-semibold"
            >
              {isSignup ? "Sign In" : "Sign Up"}
            </button>
          </p>
        </div>

        <div className="mt-8 pt-6 border-t border-gray-200 text-center text-sm text-gray-600">
          <p>🔒 Secure authentication</p>
          <p>📝 Query history saved to account</p>
          <p>🌐 Access anywhere</p>
        </div>
      </div>
    </div>
  );
}
