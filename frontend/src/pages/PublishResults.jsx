import React, { useEffect, useState } from "react";
import api from "../api/client";

const PublishResults = () => {
  const [exams, setExams] = useState([]);
  const [message, setMessage] = useState("");
  const [selectedExamId, setSelectedExamId] = useState("");
  const [students, setStudents] = useState([]);
  const [selectedStudentId, setSelectedStudentId] = useState("");

  const fetchExams = async () => {
    const response = await api.get("/exams/");
    setExams(response.data.results || response.data);
  };

  useEffect(() => {
    fetchExams();
  }, []);

  useEffect(() => {
    const loadStudents = async () => {
      const exam = exams.find((item) => String(item.id) === String(selectedExamId));
      if (!exam) {
        setStudents([]);
        return;
      }
      const response = await api.get(`/students/?class_room=${exam.class_room}`);
      setStudents(response.data.results || response.data);
    };
    if (selectedExamId) {
      loadStudents();
    }
  }, [selectedExamId, exams]);

  const publishExam = async (examId) => {
    await api.post(`/exams/${examId}/publish/`);
    setMessage("Exam published.");
    fetchExams();
  };

  const publishStudent = async () => {
    if (!selectedExamId || !selectedStudentId) {
      setMessage("Select exam and student.");
      return;
    }
    await api.post(`/exams/${selectedExamId}/publish-student/${selectedStudentId}/`);
    setMessage("Student result published.");
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

      <div className="bg-white rounded shadow mt-6 p-4 space-y-3">
        <h2 className="font-semibold">Publish Individual Student</h2>
        <div className="flex flex-wrap gap-3">
          <select value={selectedExamId} onChange={(e) => setSelectedExamId(e.target.value)} className="border rounded p-2">
            <option value="">Select Exam</option>
            {exams.map((exam) => (
              <option key={exam.id} value={exam.id}>{exam.name} {exam.term} {exam.year}</option>
            ))}
          </select>
          <select value={selectedStudentId} onChange={(e) => setSelectedStudentId(e.target.value)} className="border rounded p-2">
            <option value="">Select Student</option>
            {students.map((student) => (
              <option key={student.id} value={student.id}>
                {student.reg_no || student.id} - {student.display_name || `${student.first_name} ${student.last_name}`}
              </option>
            ))}
          </select>
          <button onClick={publishStudent} className="bg-indigo-600 text-white rounded px-4 py-2">
            Publish Student
          </button>
        </div>
      </div>
    </div>
  );
};

export default PublishResults;
