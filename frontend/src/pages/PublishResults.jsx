import React, { useEffect, useState } from "react";
import api from "../api/client";

const PublishResults = () => {
  const [exams, setExams] = useState([]);
  const [message, setMessage] = useState("");

  const fetchExams = async () => {
    const response = await api.get("/exams");
    setExams(response.data.results || response.data);
  };

  useEffect(() => {
    fetchExams();
  }, []);

  const publishExam = async (examId) => {
    await api.post(`/exams/${examId}/publish`);
    setMessage("Exam published.");
    fetchExams();
  };

  return (
    <div className="max-w-6xl mx-auto px-4 py-8">
      <h1 className="text-2xl font-semibold mb-6">Publish Results</h1>
      {message && <p className="text-green-600 mb-4">{message}</p>}
      <div className="bg-white rounded shadow">
        <table className="w-full text-sm">
          <thead className="bg-gray-100 text-left">
            <tr>
              <th className="p-2">Exam</th>
              <th className="p-2">Class</th>
              <th className="p-2">Status</th>
              <th className="p-2">Action</th>
            </tr>
          </thead>
          <tbody>
            {exams.map((exam) => (
              <tr key={exam.id} className="border-t">
                <td className="p-2">{exam.name} {exam.term} {exam.year}</td>
                <td className="p-2">{exam.class_room}</td>
                <td className="p-2">{exam.is_published ? "Published" : "Draft"}</td>
                <td className="p-2">
                  {!exam.is_published && (
                    <button
                      onClick={() => publishExam(exam.id)}
                      className="bg-indigo-600 text-white rounded px-3 py-1"
                    >
                      Publish
                    </button>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};

export default PublishResults;
