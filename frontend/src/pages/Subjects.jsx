import React, { useEffect, useState } from "react";
import api from "../api/client";

const Subjects = () => {
  const [subjects, setSubjects] = useState([]);
  const [form, setForm] = useState({ name: "", code: "", class_room: "" });

  const fetchSubjects = async () => {
    const response = await api.get("/subjects/");
    setSubjects(response.data.results || response.data);
  };

  useEffect(() => {
    fetchSubjects();
  }, []);

  const handleChange = (event) => {
    setForm({ ...form, [event.target.name]: event.target.value });
  };

  const handleSubmit = async (event) => {
    event.preventDefault();
    await api.post("/subjects/", form);
    setForm({ name: "", code: "", class_room: "" });
    fetchSubjects();
  };

  return (
    <div className="max-w-6xl mx-auto px-4 py-8">
      <h1 className="text-2xl font-semibold mb-6">Subjects</h1>
      <form onSubmit={handleSubmit} className="bg-white p-4 rounded shadow mb-6 grid grid-cols-1 md:grid-cols-4 gap-4">
        <input name="name" value={form.name} onChange={handleChange} placeholder="Subject name" className="border rounded p-2" />
        <input name="code" value={form.code} onChange={handleChange} placeholder="Code" className="border rounded p-2" />
        <input name="class_room" value={form.class_room} onChange={handleChange} placeholder="Class ID" className="border rounded p-2" />
        <button className="bg-indigo-600 text-white rounded px-4">Add Subject</button>
      </form>
      <table className="w-full bg-white rounded shadow text-sm">
        <thead className="bg-gray-100 text-left">
          <tr>
            <th className="p-2">Name</th>
            <th className="p-2">Code</th>
            <th className="p-2">Class</th>
          </tr>
        </thead>
        <tbody>
          {subjects.map((subject) => (
            <tr key={subject.id} className="border-t">
              <td className="p-2">{subject.name}</td>
              <td className="p-2">{subject.code}</td>
              <td className="p-2">{subject.class_room}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
};

export default Subjects;
