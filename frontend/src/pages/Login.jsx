import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../auth/AuthContext";

const Login = () => {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const { login } = useAuth();
  const navigate = useNavigate();

  const handleSubmit = async (event) => {
    event.preventDefault();
    setError("");
    try {
      await login(username, password);
      navigate("/");
    } catch (err) {
      setError("Invalid credentials. Please try again.");
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-100">
      <form onSubmit={handleSubmit} className="bg-white p-8 rounded shadow w-full max-w-sm">
        <h1 className="text-xl font-semibold mb-6">Login</h1>
        {error && <p className="text-red-600 mb-4 text-sm">{error}</p>}
        <label className="block text-sm mb-2">Username</label>
        <input
          className="w-full rounded border p-2 mb-4"
          value={username}
          onChange={(e) => setUsername(e.target.value)}
        />
        <label className="block text-sm mb-2">Password</label>
        <input
          type="password"
          className="w-full rounded border p-2 mb-6"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
        />
        <button className="w-full bg-indigo-600 text-white py-2 rounded">Login</button>
      </form>
    </div>
  );
};

export default Login;
