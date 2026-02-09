import React from "react";
import { Routes, Route } from "react-router-dom";
import NavBar from "./components/NavBar";
import ProtectedRoute from "./components/ProtectedRoute";
import Login from "./pages/Login";
import Dashboard from "./pages/Dashboard";
import Students from "./pages/Students";
import Classes from "./pages/Classes";
import Subjects from "./pages/Subjects";
import UploadResults from "./pages/UploadResults";
import PublishResults from "./pages/PublishResults";
import ParentResult from "./pages/ParentResult";
import ClassResults from "./pages/ClassResults";
import PublicClassResults from "./pages/PublicClassResults";
import Analytics from "./pages/Analytics";

const App = () => {
  return (
    <div className="min-h-screen">
      <NavBar />
      <Routes>
        <Route path="/login" element={<Login />} />
        <Route
          path="/"
          element={
            <ProtectedRoute>
              <Dashboard />
            </ProtectedRoute>
          }
        />
        <Route
          path="/students"
          element={
            <ProtectedRoute permissions={["crud_student"]}>
              <Students />
            </ProtectedRoute>
          }
        />
        <Route
          path="/classes"
          element={
            <ProtectedRoute permissions={["crud_class"]}>
              <Classes />
            </ProtectedRoute>
          }
        />
        <Route
          path="/subjects"
          element={
            <ProtectedRoute permissions={["crud_subject"]}>
              <Subjects />
            </ProtectedRoute>
          }
        />
        <Route
          path="/upload-results"
          element={
            <ProtectedRoute permissions={["upload_result"]}>
              <UploadResults />
            </ProtectedRoute>
          }
        />
        <Route
          path="/publish-results"
          element={
            <ProtectedRoute permissions={["publish_result"]}>
              <PublishResults />
            </ProtectedRoute>
          }
        />
        <Route
          path="/parent-result"
          element={
            <ProtectedRoute permissions={["view_student_result"]}>
              <ParentResult />
            </ProtectedRoute>
          }
        />
        <Route
          path="/class-results"
          element={
            <ProtectedRoute permissions={["view_class_result"]}>
              <ClassResults />
            </ProtectedRoute>
          }
        />
        <Route path="/public/class-results" element={<PublicClassResults />} />
        <Route
          path="/analytics"
          element={
            <ProtectedRoute permissions={["view_analytics"]}>
              <Analytics />
            </ProtectedRoute>
          }
        />
      </Routes>
    </div>
  );
};

export default App;
