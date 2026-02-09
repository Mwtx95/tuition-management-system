import React, { useState } from "react";
import api from "../api/client";

const Analytics = () => {
  const [classId, setClassId] = useState("");
  const [examId, setExamId] = useState("");
  const [data, setData] = useState(null);

  const fetchAnalytics = async () => {
    const response = await api.get(`/analytics/class/${classId}/?exam_id=${examId}`);
    setData(response.data);
  };

  return (
    <div className="max-w-6xl mx-auto px-4 py-8">
      <h1 className="text-2xl font-semibold mb-6">Analytics Dashboard</h1>
      <div className="bg-white p-4 rounded shadow mb-6 flex flex-wrap gap-4">
        <input value={classId} onChange={(e) => setClassId(e.target.value)} placeholder="Class ID" className="border rounded p-2" />
        <input value={examId} onChange={(e) => setExamId(e.target.value)} placeholder="Exam ID" className="border rounded p-2" />
        <button onClick={fetchAnalytics} className="bg-indigo-600 text-white rounded px-4 py-2">View</button>
      </div>
      {data && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div className="bg-white p-4 rounded shadow">
            <h2 className="font-semibold">Class Average</h2>
            <p className="text-2xl mt-2">{Number(data.class_average).toFixed(2)}</p>
          </div>
          <div className="bg-white p-4 rounded shadow">
            <h2 className="font-semibold">Pass/Fail</h2>
            <p className="mt-2">Pass: {data.pass_fail_rate.pass}</p>
            <p>Fail: {data.pass_fail_rate.fail}</p>
          </div>
          <div className="bg-white p-4 rounded shadow md:col-span-2">
            <h2 className="font-semibold mb-2">Top Students</h2>
            <ul className="list-disc list-inside">
              {data.top_students.map((student) => (
                <li key={student.id}>{student.name} - {student.total}</li>
              ))}
            </ul>
          </div>
        </div>
      )}
    </div>
  );
};

export default Analytics;
