import { useState } from "react";
import toast from "react-hot-toast";
import { uploadDataset } from "../api/dataset";

export default function UploadForm({ onUploaded }) {
  const [file, setFile] = useState(null);
  const [name, setName] = useState("");
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();

    if (!file) {
      toast.error("Choose a CSV file");
      return;
    }

    if (!name.trim()) {
      toast.error("Enter a dataset name");
      return;
    }

    if (loading) return;

    setLoading(true);

    try {
      const formData = new FormData();
      formData.append("file", file);
      formData.append("name", name);

      await uploadDataset(formData);

      toast.success("Upload successful");

      setFile(null);
      setName("");

      e.target.reset();

      onUploaded?.();
    } catch (err) {
      const detail = err.response?.data?.detail;

      const message = Array.isArray(detail)
        ? detail.map((e) => e.msg).join(", ")
        : detail || err.message || "Upload failed";

      toast.error(message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <form onSubmit={handleSubmit}>
      <input
        type="text"
        placeholder="Dataset name"
        value={name}
        onChange={(e) => setName(e.target.value)}
        style={{
          display: "block",
          marginBottom: "10px",
          width: "100%",
          padding: "8px",
        }}
      />

      <input
        type="file"
        accept=".csv"
        onChange={(e) => setFile(e.target.files[0])}
        style={{ display: "block", marginBottom: "12px" }}
      />

      <button type="submit" disabled={loading}>
        {loading ? "Uploading..." : "Upload"}
      </button>
    </form>
  );
}