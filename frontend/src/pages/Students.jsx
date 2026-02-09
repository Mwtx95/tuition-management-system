import React, { useEffect, useState } from "react";
import api from "../api/client";

const Students = () => {
  const [students, setStudents] = useState([]);
  const [form, setForm] = useState({
    full_name: "",
    gender: "M",
    age: "",
    class_room: "",
    parent: "",
    address: ""
  });

  const fetchStudents = async () => {
    const response = await api.get("/students/");
    setStudents(response.data.results || response.data);
  };

  useEffect(() => {
    fetchStudents();
  }, []);

  const handleChange = (event) => {
    setForm({ ...form, [event.target.name]: event.target.value });
  };

  const handleSubmit = async (event) => {
    event.preventDefault();
    await api.post("/students/", form);
    setForm({
      full_name: "",
      gender: "M",
      age: "",
      class_room: "",
      parent: "",
      address: ""
    });
    fetchStudents();
  };

  return (
    <div className="max-w-6xl mx-auto px-4 py-8">
      <h1 className="text-2xl font-semibold mb-6">Students</h1>
      <form onSubmit={handleSubmit} className="bg-white p-4 rounded shadow mb-6 grid grid-cols-1 md:grid-cols-6 gap-4">
        <input name="full_name" value={form.full_name} onChange={handleChange} placeholder="Full name" className="border rounded p-2 md:col-span-2" />
        <select name="gender" value={form.gender} onChange={handleChange} className="border rounded p-2">
          <option value="M">Male</option>
          <option value="F">Female</option>
        </select>
        <input name="age" value={form.age} onChange={handleChange} placeholder="Age" className="border rounded p-2" />
        <input name="class_room" value={form.class_room} onChange={handleChange} placeholder="Class ID" className="border rounded p-2" />
        <input name="parent" value={form.parent} onChange={handleChange} placeholder="Parent ID" className="border rounded p-2" />
        <input name="address" value={form.address} onChange={handleChange} placeholder="Address (optional)" className="border rounded p-2 md:col-span-2" />
        <button className="bg-indigo-600 text-white rounded px-4 py-2 md:col-span-6">Add Student</button>
      </form>
      <div className="bg-white rounded shadow">
        <table className="w-full text-sm">
          <thead className="bg-gray-100 text-left">
            <tr>
              <th className="p-2">Reg No</th>
              <th className="p-2">Name</th>
              <th className="p-2">Gender</th>
              <th className="p-2">Age</th>
              <th className="p-2">Class</th>
            </tr>
          </thead>
          <tbody>
            {students.map((student) => (
              <tr key={student.id} className="border-t">
                <td className="p-2">{student.reg_no}</td>
                <td className="p-2">{student.display_name || `${student.first_name} ${student.last_name}`}</td>
                <td className="p-2">{student.gender}</td>
                <td className="p-2">{student.age}</td>
                <td className="p-2">{student.class_room}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};

export default Students;
