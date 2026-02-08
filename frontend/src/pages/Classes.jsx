import React, { useEffect, useState } from "react";
import api from "../api/client";

const Classes = () => {
  const [classes, setClasses] = useState([]);
  const [name, setName] = useState("");

  const fetchClasses = async () => {
    const response = await api.get("/classes");
    setClasses(response.data.results || response.data);
  };

  useEffect(() => {
    fetchClasses();
  }, []);

  const handleSubmit = async (event) => {
    event.preventDefault();
    await api.post("/classes", { name });
    setName("");
    fetchClasses();
  };

  return (
    <div className="max-w-6xl mx-auto px-4 py-8">
      <h1 className="text-2xl font-semibold mb-6">Classes</h1>
      <form onSubmit={handleSubmit} className="bg-white p-4 rounded shadow mb-6 flex gap-4">
        <input value={name} onChange={(e) => setName(e.target.value)} placeholder="Class name" className="border rounded p-2 flex-1" />
        <button className="bg-indigo-600 text-white rounded px-4">Add Class</button>
      </form>
      <ul className="bg-white rounded shadow divide-y">
        {classes.map((classRoom) => (
          <li key={classRoom.id} className="p-3">{classRoom.name}</li>
        ))}
      </ul>
    </div>
  );
};

export default Classes;
