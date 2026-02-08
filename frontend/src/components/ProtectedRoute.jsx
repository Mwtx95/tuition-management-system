import React from "react";
import { Navigate } from "react-router-dom";
import { useAuth } from "../auth/AuthContext";

const ProtectedRoute = ({ children, permissions = [] }) => {
  const { user, loading } = useAuth();
  if (loading) {
    return <div className="p-6">Loading...</div>;
  }
  if (!user) {
    return <Navigate to="/login" replace />;
  }
  if (permissions.length > 0) {
    const hasPermission = permissions.every((permission) => user.permissions?.includes(permission));
    if (!hasPermission) {
      return <div className="p-6 text-red-600">Access denied.</div>;
    }
  }
  return children;
};

export default ProtectedRoute;
