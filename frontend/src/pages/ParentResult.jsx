import React, { useState } from "react";
import api from "../api/client";

const ParentResult = () => {
  const [studentId, setStudentId] = useState("");
  const [examId, setExamId] = useState("");
  const [results, setResults] = useState([]);

  const fetchResults = async () => {
    const response = await api.get(`/results/student/${studentId}?exam_id=${examId}`);
    setResults(response.data);
  };

  const downloadPdf = () => {
    window.open(`${import.meta.env.VITE_API_URL || "http://localhost:8000/api"}/report-card/${studentId}/${examId}/pdf`, "_blank");
  };

  return (
    <div className="max-w-6xl mx-auto px-4 py-8">
      <h1 className="text-2xl font-semibold mb-6">Parent Result View</h1>
      <div className="bg-white p-4 rounded shadow mb-6 flex flex-wrap gap-4">
        <input value={studentId} onChange={(e) => setStudentId(e.target.value)} placeholder="Student ID" className="border rounded p-2" />
        <input value={examId} onChange={(e) => setExamId(e.target.value)} placeholder="Exam ID" className="border rounded p-2" />
        <button onClick={fetchResults} className="bg-indigo-600 text-white rounded px-4 py-2">View</button>
        <button onClick={downloadPdf} className="bg-gray-800 text-white rounded px-4 py-2">Download PDF</button>
      </div>
      <div className="bg-white rounded shadow">
        <table className="w-full text-sm">
          <thead className="bg-gray-100 text-left">
            <tr>
              <th className="p-2">Subject</th>
              <th className="p-2">Marks</th>
              <th className="p-2">Grade</th>
            </tr>
          </thead>
          <tbody>
            {results.map((result) => (
              <tr key={result.id} className="border-t">
                <td className="p-2">{result.subject}</td>
                <td className="p-2">{result.marks}</td>
                <td className="p-2">{result.grade}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};

export default ParentResult;
