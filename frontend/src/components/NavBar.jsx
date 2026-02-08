import React from "react";
import { Link } from "react-router-dom";
import { useAuth } from "../auth/AuthContext";

const NavBar = () => {
  const { user, logout } = useAuth();
  return (
    <nav className="bg-white shadow-sm">
      <div className="mx-auto max-w-6xl px-4 py-4 flex items-center justify-between">
        <Link to="/" className="font-semibold text-indigo-600">
          Tuition Management
        </Link>
        {user ? (
          <div className="flex items-center gap-4">
            <span className="text-sm text-gray-600">{user.username}</span>
            <button
              className="rounded bg-indigo-600 px-3 py-1 text-white text-sm"
              onClick={logout}
            >
              Logout
            </button>
          </div>
        ) : (
          <Link className="text-sm text-indigo-600" to="/login">
            Login
          </Link>
        )}
      </div>
    </nav>
  );
};

export default NavBar;
