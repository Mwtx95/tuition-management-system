import React, { useEffect, useMemo, useState } from "react";
import api from "../api/client";
import { useAuth } from "../auth/AuthContext";

const UploadResults = () => {
  const { user } = useAuth();
  const [classes, setClasses] = useState([]);
  const [exams, setExams] = useState([]);
  const [allSubjects, setAllSubjects] = useState([]);
  const [mySubjects, setMySubjects] = useState([]);
  const [classId, setClassId] = useState("");
  const [examId, setExamId] = useState("");
  const [csvFile, setCsvFile] = useState(null);
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");
  const [subjectId, setSubjectId] = useState("");
  const [subjectExamId, setSubjectExamId] = useState("");
  const [sheetRows, setSheetRows] = useState([]);
  const [sheetMessage, setSheetMessage] = useState("");
  const [sheetError, setSheetError] = useState("");
  const [allSheetClassId, setAllSheetClassId] = useState("");
  const [allSheetExamId, setAllSheetExamId] = useState("");
  const [allSheet, setAllSheet] = useState({ subjects: [], rows: [] });
  const [allSheetMessage, setAllSheetMessage] = useState("");
  const [allSheetError, setAllSheetError] = useState("");

  const gradeForMarks = (value) => {
    if (value === null || value === undefined || value === "") return "";
    const score = Number(value);
    if (Number.isNaN(score)) return "";
    if (score >= 81) return "A";
    if (score >= 61) return "B";
    if (score >= 41) return "C";
    if (score >= 21) return "D";
    return "F";
  };

  useEffect(() => {
    const load = async () => {
      const [classesResponse, examsResponse, allSubjectsResponse, mySubjectsResponse] = await Promise.all([
        api.get("/classes/"),
        api.get("/exams/"),
        api.get("/subjects/"),
        api.get(user?.id ? `/subjects/?teacher=${user.id}` : "/subjects/")
      ]);
      setClasses(classesResponse.data.results || classesResponse.data);
      setExams(examsResponse.data.results || examsResponse.data);
      const all = allSubjectsResponse.data.results || allSubjectsResponse.data;
      const mine = mySubjectsResponse.data.results || mySubjectsResponse.data;
      setAllSubjects(all);
      setMySubjects(mine);
    };
    load();
  }, [user]);

  const filteredExams = useMemo(() => {
    if (!classId) return exams;
    return exams.filter((exam) => String(exam.class_room) === String(classId));
  }, [classId, exams]);

  const selectedSubject = useMemo(
    () => allSubjects.find((subject) => String(subject.id) === String(subjectId)),
    [allSubjects, subjectId]
  );

  const subjectExams = useMemo(() => {
    if (!selectedSubject) return exams;
    return exams.filter((exam) => String(exam.class_room) === String(selectedSubject.class_room));
  }, [selectedSubject, exams]);

  const allSheetExams = useMemo(() => {
    if (!allSheetClassId) return exams;
    return exams.filter((exam) => String(exam.class_room) === String(allSheetClassId));
  }, [allSheetClassId, exams]);

  const downloadTemplate = async () => {
    if (!classId || !examId) {
      setError("Select class and exam before downloading the template.");
      return;
    }
    try {
      setMessage("");
      setError("");
      const response = await api.get(`/results/class/${classId}/csv-template/?exam_id=${examId}`, {
        responseType: "blob"
      });
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement("a");
      link.href = url;
      link.download = `results_template_class_${classId}_exam_${examId}.csv`;
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);
    } catch (err) {
      setError(err?.response?.data?.detail || "Failed to download template.");
    }
  };

  const handleCsvUpload = async () => {
    if (!classId || !examId) {
      setError("Select class and exam before uploading.");
      return;
    }
    if (!csvFile) {
      setError("Choose a CSV file to upload.");
      return;
    }
    try {
      setMessage("");
      setError("");
      const formData = new FormData();
      formData.append("file", csvFile);
      const response = await api.post(`/results/class/${classId}/csv-import/?exam_id=${examId}`, formData, {
        headers: { "Content-Type": "multipart/form-data" }
      });
      setMessage(`CSV import complete. Created: ${response.data.created}, Updated: ${response.data.updated}`);
    } catch (err) {
      const detail = err?.response?.data?.detail;
      setError(detail || "Failed to import CSV.");
    }
  };

  const loadSubjectSheet = async () => {
    if (!subjectId || !subjectExamId) {
      setSheetError("Select subject and exam.");
      return;
    }
    try {
      setSheetMessage("");
      setSheetError("");
      const response = await api.get(`/results/subject/${subjectId}/sheet/?exam_id=${subjectExamId}`);
      setSheetRows(response.data.rows || []);
    } catch (err) {
      setSheetError(err?.response?.data?.detail || "Failed to load subject sheet.");
    }
  };

  const updateMark = (index, value) => {
    const next = [...sheetRows];
    next[index] = { ...next[index], marks: value };
    setSheetRows(next);
  };

  const saveSubjectSheet = async () => {
    if (!subjectId || !subjectExamId) {
      setSheetError("Select subject and exam.");
      return;
    }
    try {
      setSheetMessage("");
      setSheetError("");
      const payload = {
        rows: sheetRows.map((row) => ({
          student_id: row.student_id,
          reg_no: row.reg_no,
          marks: row.marks
        }))
      };
      const response = await api.post(`/results/subject/${subjectId}/sheet/?exam_id=${subjectExamId}`, payload);
      setSheetMessage(`Saved. Created: ${response.data.created}, Updated: ${response.data.updated}`);
    } catch (err) {
      const detail = err?.response?.data?.detail;
      setSheetError(detail || "Failed to save subject sheet.");
    }
  };

  const loadAllSubjectSheet = async () => {
    if (!allSheetClassId || !allSheetExamId) {
      setAllSheetError("Select class and exam.");
      return;
    }
    try {
      setAllSheetMessage("");
      setAllSheetError("");
      const response = await api.get(`/results/class/${allSheetClassId}/sheet/?exam_id=${allSheetExamId}`);
      setAllSheet(response.data);
    } catch (err) {
      setAllSheetError(err?.response?.data?.detail || "Failed to load class sheet.");
    }
  };

  const updateAllSheetMark = (rowIndex, subjectIndex, value) => {
    const nextRows = [...allSheet.rows];
    const row = { ...nextRows[rowIndex] };
    const subjects = [...row.subjects];
    subjects[subjectIndex] = {
      ...subjects[subjectIndex],
      marks: value
    };
    row.subjects = subjects;
    nextRows[rowIndex] = row;
    setAllSheet({ ...allSheet, rows: nextRows });
  };

  const saveAllSubjectSheet = async () => {
    if (!allSheetClassId || !allSheetExamId) {
      setAllSheetError("Select class and exam.");
      return;
    }
    try {
      setAllSheetMessage("");
      setAllSheetError("");
      const results = [];
      allSheet.rows.forEach((row) => {
        row.subjects.forEach((subject, index) => {
          const rawMarks = String(subject.marks || "").trim();
          if (rawMarks === "") {
            return;
          }
          results.push({
            student: row.student_id,
            subject: allSheet.subjects[index]?.id,
            exam: allSheetExamId,
            marks: rawMarks
          });
        });
      });
      if (results.length === 0) {
        setAllSheetError("No marks entered.");
        return;
      }
      const response = await api.post("/results/bulk-upload/", { results });
      setAllSheetMessage(`Saved. Created: ${response.data.created}, Updated: ${response.data.updated}`);
    } catch (err) {
      const detail = err?.response?.data?.detail;
      setAllSheetError(detail || "Failed to save class sheet.");
    }
  };

  return (
    <div className="max-w-6xl mx-auto px-4 py-8">
      <h1 className="text-2xl font-semibold mb-6">Upload Results</h1>
      {message && <p className="mb-4 text-green-600">{message}</p>}
      {error && <p className="mb-4 text-red-600">{error}</p>}
      <div className="grid grid-cols-1 gap-6">
        <div className="bg-white p-4 rounded shadow space-y-3">
          <h2 className="font-semibold">CSV Template & Import</h2>
          <p className="text-sm text-gray-500">Download the Excel-style template, fill marks, then upload the CSV.</p>
          <select value={classId} onChange={(e) => setClassId(e.target.value)} className="border rounded p-2 w-full">
            <option value="">Select Class</option>
            {classes.map((item) => (
              <option key={item.id} value={item.id}>{item.name}</option>
            ))}
          </select>
          <select value={examId} onChange={(e) => setExamId(e.target.value)} className="border rounded p-2 w-full">
            <option value="">Select Exam</option>
            {filteredExams.map((item) => (
              <option key={item.id} value={item.id}>{item.name} {item.term} {item.year}</option>
            ))}
          </select>
          <div className="flex flex-wrap gap-2">
            <button onClick={downloadTemplate} className="bg-gray-800 text-white rounded px-4 py-2">Download Template</button>
            <label className="inline-flex items-center gap-2 bg-gray-100 border rounded px-3 py-2 cursor-pointer">
              <input type="file" accept=".csv" className="hidden" onChange={(e) => setCsvFile(e.target.files?.[0] || null)} />
              <span>{csvFile ? csvFile.name : "Choose CSV File"}</span>
            </label>
            <button onClick={handleCsvUpload} className="bg-indigo-600 text-white rounded px-4 py-2">
              Upload CSV
            </button>
          </div>
        </div>
      </div>

      <div className="bg-white p-4 rounded shadow mt-6 space-y-4">
        <div className="flex flex-wrap items-center gap-3">
          <h2 className="font-semibold">Teacher Sheet (Editable Table)</h2>
          {sheetMessage && <span className="text-sm text-green-600">{sheetMessage}</span>}
          {sheetError && <span className="text-sm text-red-600">{sheetError}</span>}
        </div>
        <div className="flex flex-wrap gap-2">
          <select value={subjectId} onChange={(e) => setSubjectId(e.target.value)} className="border rounded p-2">
            <option value="">Select Subject</option>
            {mySubjects.length > 0 && (
              <optgroup label="My Subjects">
                {mySubjects.map((item) => (
                  <option key={`mine-${item.id}`} value={item.id}>{item.name} ({item.code})</option>
                ))}
              </optgroup>
            )}
            {allSubjects.length > 0 && (
              <optgroup label="All Subjects">
                {allSubjects
                  .filter((item) => !mySubjects.some((mine) => String(mine.id) === String(item.id)))
                  .map((item) => (
                    <option key={`all-${item.id}`} value={item.id}>{item.name} ({item.code})</option>
                  ))}
              </optgroup>
            )}
          </select>
          <select value={subjectExamId} onChange={(e) => setSubjectExamId(e.target.value)} className="border rounded p-2">
            <option value="">Select Exam</option>
            {subjectExams.map((item) => (
              <option key={item.id} value={item.id}>{item.name} {item.term} {item.year}</option>
            ))}
          </select>
          <button onClick={loadSubjectSheet} className="bg-gray-800 text-white rounded px-4 py-2">Load Sheet</button>
          <button onClick={saveSubjectSheet} className="bg-indigo-600 text-white rounded px-4 py-2">Save Sheet</button>
        </div>

        {sheetRows.length > 0 && (
          <div className="overflow-x-auto border rounded">
            <table className="w-full text-sm">
              <thead className="bg-gray-100 text-left">
                <tr>
                  <th className="p-2">Reg No</th>
                  <th className="p-2">Student</th>
                  <th className="p-2">Gender</th>
                  <th className="p-2">Marks</th>
                  <th className="p-2">Grade</th>
                </tr>
              </thead>
              <tbody>
                {sheetRows.map((row, index) => (
                  <tr key={row.student_id} className="border-t">
                    <td className="p-2">{row.reg_no || row.student_id}</td>
                    <td className="p-2">{row.full_name}</td>
                    <td className="p-2">{row.gender}</td>
                    <td className="p-2">
                      <input
                        type="number"
                        min="0"
                        max="100"
                        value={row.marks}
                        onChange={(e) => updateMark(index, e.target.value)}
                        className="border rounded p-1 w-24"
                        placeholder="Marks"
                      />
                    </td>
                    <td className="p-2">{gradeForMarks(row.marks)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      <div className="bg-white p-4 rounded shadow mt-6 space-y-4">
        <div className="flex flex-wrap items-center gap-3">
          <h2 className="font-semibold">All Subjects Sheet (Editable Grid)</h2>
          {allSheetMessage && <span className="text-sm text-green-600">{allSheetMessage}</span>}
          {allSheetError && <span className="text-sm text-red-600">{allSheetError}</span>}
        </div>
        <div className="flex flex-wrap gap-2">
          <select value={allSheetClassId} onChange={(e) => setAllSheetClassId(e.target.value)} className="border rounded p-2">
            <option value="">Select Class</option>
            {classes.map((item) => (
              <option key={item.id} value={item.id}>{item.name}</option>
            ))}
          </select>
          <select value={allSheetExamId} onChange={(e) => setAllSheetExamId(e.target.value)} className="border rounded p-2">
            <option value="">Select Exam</option>
            {allSheetExams.map((item) => (
              <option key={item.id} value={item.id}>{item.name} {item.term} {item.year}</option>
            ))}
          </select>
          <button onClick={loadAllSubjectSheet} className="bg-gray-800 text-white rounded px-4 py-2">Load Sheet</button>
          <button onClick={saveAllSubjectSheet} className="bg-indigo-600 text-white rounded px-4 py-2">Save Sheet</button>
        </div>

        {allSheet.rows.length > 0 && (
          <div className="overflow-x-auto border rounded">
            <table className="w-full text-sm">
              <thead className="bg-gray-100 text-left">
                <tr>
                  <th className="p-2">Reg No</th>
                  <th className="p-2">Student</th>
                  <th className="p-2">Gender</th>
                  {allSheet.subjects.map((subject) => (
                    <th key={subject.id} className="p-2">{subject.header}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {allSheet.rows.map((row, rowIndex) => (
                  <tr key={row.student_id} className="border-t">
                    <td className="p-2">{row.reg_no || row.student_id}</td>
                    <td className="p-2">{row.full_name}</td>
                    <td className="p-2">{row.gender}</td>
                    {row.subjects.map((subject, subjectIndex) => (
                      <td key={`${row.student_id}-${subjectIndex}`} className="p-2">
                        <input
                          type="number"
                          min="0"
                          max="100"
                          value={subject.marks}
                          onChange={(e) => updateAllSheetMark(rowIndex, subjectIndex, e.target.value)}
                          className="border rounded p-1 w-20"
                          placeholder="Marks"
                        />
                        <div className="text-xs text-gray-500 mt-1">
                          Grade: {gradeForMarks(subject.marks) || "-"}
                        </div>
                      </td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
};

export default UploadResults;
