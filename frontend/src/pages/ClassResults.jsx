import React, { useState } from "react";
import api from "../api/client";

const ClassResults = () => {
  const [classId, setClassId] = useState("");
  const [examId, setExamId] = useState("");
  const [data, setData] = useState({ results: [], totals: [], rankings: {} });

  const fetchResults = async () => {
    const response = await api.get(`/results/class/${classId}?exam_id=${examId}`);
    setData(response.data);
  };

  return (
    <div className="max-w-6xl mx-auto px-4 py-8">
      <h1 className="text-2xl font-semibold mb-6">Class Result Sheet</h1>
      <div className="bg-white p-4 rounded shadow mb-6 flex flex-wrap gap-4">
        <input value={classId} onChange={(e) => setClassId(e.target.value)} placeholder="Class ID" className="border rounded p-2" />
        <input value={examId} onChange={(e) => setExamId(e.target.value)} placeholder="Exam ID" className="border rounded p-2" />
        <button onClick={fetchResults} className="bg-indigo-600 text-white rounded px-4 py-2">View</button>
      </div>
      <div className="bg-white rounded shadow">
        <table className="w-full text-sm">
          <thead className="bg-gray-100 text-left">
            <tr>
              <th className="p-2">Student</th>
              <th className="p-2">Subject</th>
              <th className="p-2">Marks</th>
              <th className="p-2">Grade</th>
              <th className="p-2">Rank</th>
            </tr>
          </thead>
          <tbody>
            {data.results.map((result) => (
              <tr key={result.id} className="border-t">
                <td className="p-2">{result.student}</td>
                <td className="p-2">{result.subject}</td>
                <td className="p-2">{result.marks}</td>
                <td className="p-2">{result.grade}</td>
                <td className="p-2">{data.rankings[result.student]}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};

export default ClassResults;
