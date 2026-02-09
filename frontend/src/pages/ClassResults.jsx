import React, { useState } from "react";
import api from "../api/client";

const ClassResults = () => {
  const [classId, setClassId] = useState("");
  const [examId, setExamId] = useState("");
  const [sheet, setSheet] = useState({ subjects: [], rows: [] });
  const [error, setError] = useState("");

  const fetchResults = async () => {
    try {
      setError("");
      const response = await api.get(`/results/class/${classId}/sheet?exam_id=${examId}`);
      setSheet(response.data);
    } catch (err) {
      setError(err?.response?.data?.detail || "Failed to load class results.");
    }
  };

  return (
    <div className="max-w-6xl mx-auto px-4 py-8">
      <h1 className="text-2xl font-semibold mb-6">Class Result Sheet</h1>
      {error && <p className="mb-4 text-red-600">{error}</p>}
      <div className="bg-white p-4 rounded shadow mb-6 flex flex-wrap gap-4">
        <input value={classId} onChange={(e) => setClassId(e.target.value)} placeholder="Class ID" className="border rounded p-2" />
        <input value={examId} onChange={(e) => setExamId(e.target.value)} placeholder="Exam ID" className="border rounded p-2" />
        <button onClick={fetchResults} className="bg-indigo-600 text-white rounded px-4 py-2">View</button>
      </div>
      <div className="bg-white rounded shadow overflow-x-auto">
        <table className="w-full text-sm">
          <thead className="bg-gray-100 text-left">
            <tr>
              <th className="p-2">Student ID</th>
              <th className="p-2">Full Name</th>
              <th className="p-2">Gender</th>
              {sheet.subjects.map((subject) => (
                <React.Fragment key={subject.id}>
                  <th className="p-2">{subject.header}</th>
                  <th className="p-2">{subject.header} Grade</th>
                </React.Fragment>
              ))}
              <th className="p-2">Total</th>
              <th className="p-2">Avg</th>
              <th className="p-2">Avg Grade</th>
              <th className="p-2">Remarks</th>
              <th className="p-2">Rank</th>
            </tr>
          </thead>
          <tbody>
            {sheet.rows.map((row) => (
              <tr key={row.student_id} className="border-t">
                <td className="p-2">{row.student_id}</td>
                <td className="p-2">{row.full_name}</td>
                <td className="p-2">{row.gender}</td>
                {row.subjects.map((subject, index) => (
                  <React.Fragment key={`${row.student_id}-${index}`}>
                    <td className="p-2">{subject.marks}</td>
                    <td className="p-2">{subject.grade}</td>
                  </React.Fragment>
                ))}
                <td className="p-2">{row.total}</td>
                <td className="p-2">{row.average}</td>
                <td className="p-2">{row.average_grade}</td>
                <td className="p-2">{row.remarks}</td>
                <td className="p-2">{row.rank}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};

export default ClassResults;
