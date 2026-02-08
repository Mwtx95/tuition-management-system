import React, { useState } from "react";
import api from "../api/client";

const UploadResults = () => {
  const [single, setSingle] = useState({ student: "", subject: "", exam: "", marks: "" });
  const [bulkData, setBulkData] = useState("[]");
  const [message, setMessage] = useState("");

  const handleSingleChange = (event) => {
    setSingle({ ...single, [event.target.name]: event.target.value });
  };

  const handleSingleSubmit = async (event) => {
    event.preventDefault();
    await api.post("/results/upload", single);
    setMessage("Result uploaded.");
  };

  const handleBulkSubmit = async () => {
    const parsed = JSON.parse(bulkData);
    await api.post("/results/bulk-upload", { results: parsed });
    setMessage("Bulk results uploaded.");
  };

  return (
    <div className="max-w-6xl mx-auto px-4 py-8">
      <h1 className="text-2xl font-semibold mb-6">Upload Results</h1>
      {message && <p className="mb-4 text-green-600">{message}</p>}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <form onSubmit={handleSingleSubmit} className="bg-white p-4 rounded shadow space-y-3">
          <h2 className="font-semibold">Single Upload</h2>
          <input name="student" value={single.student} onChange={handleSingleChange} placeholder="Student ID" className="border rounded p-2 w-full" />
          <input name="subject" value={single.subject} onChange={handleSingleChange} placeholder="Subject ID" className="border rounded p-2 w-full" />
          <input name="exam" value={single.exam} onChange={handleSingleChange} placeholder="Exam ID" className="border rounded p-2 w-full" />
          <input name="marks" value={single.marks} onChange={handleSingleChange} placeholder="Marks" className="border rounded p-2 w-full" />
          <button className="bg-indigo-600 text-white rounded px-4 py-2">Upload</button>
        </form>
        <div className="bg-white p-4 rounded shadow space-y-3">
          <h2 className="font-semibold">Bulk Upload</h2>
          <p className="text-sm text-gray-500">Paste an array of results with student, subject, exam, marks.</p>
          <textarea
            value={bulkData}
            onChange={(e) => setBulkData(e.target.value)}
            className="border rounded p-2 w-full h-48"
          />
          <button onClick={handleBulkSubmit} className="bg-indigo-600 text-white rounded px-4 py-2">
            Upload Bulk
          </button>
        </div>
      </div>
    </div>
  );
};

export default UploadResults;
