import React from "react";
import { Link } from "react-router-dom";
import { useAuth } from "../auth/AuthContext";

const Dashboard = () => {
  const { user } = useAuth();

  const cards = [
    { label: "Students", to: "/students", permission: "crud_student" },
    { label: "Classes", to: "/classes", permission: "crud_class" },
    { label: "Subjects", to: "/subjects", permission: "crud_subject" },
    { label: "Upload Results", to: "/upload-results", permission: "upload_result" },
    { label: "Publish Results", to: "/publish-results", permission: "publish_result" },
    { label: "Class Result Sheet", to: "/class-results", permission: "view_class_result" },
    { label: "Parent View", to: "/parent-result", permission: "view_student_result" },
    { label: "Analytics", to: "/analytics", permission: "view_analytics" }
  ];

  return (
    <div className="max-w-6xl mx-auto px-4 py-8">
      <h1 className="text-2xl font-semibold mb-6">Welcome {user?.username}</h1>
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {cards
          .filter((card) => user?.permissions?.includes(card.permission))
          .map((card) => (
            <Link
              key={card.label}
              to={card.to}
              className="rounded-lg border bg-white p-6 shadow hover:shadow-md"
            >
              <h2 className="text-lg font-semibold text-indigo-600">{card.label}</h2>
              <p className="text-sm text-gray-500 mt-2">Manage {card.label.toLowerCase()} workflows.</p>
            </Link>
          ))}
      </div>
    </div>
  );
};

export default Dashboard;
