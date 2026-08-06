import { useState } from "react";
import toast from "react-hot-toast";
import { uploadDataset } from "../api/dataset";

export default function UploadForm({ onUploaded }) {
  const [file, setFile] = useState(null);
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!file || loading) return;

    setLoading(true);
    try {
      const formData = new FormData();
      formData.append("file", file);

      await uploadDataset(formData);
      toast.success("Upload successful");
      setFile(null);
      onUploaded?.();
    } catch (err) {
      const detail = err.response?.data?.detail;
      const message = Array.isArray(detail)
        ? detail.map((e) => e.msg).join(", ")
        : detail || err.message || "Upload failed";

      toast.error(message);
      console.log(err.response?.status);
      console.log(err.response?.data);
    } finally {
      setLoading(false);
    }
  };

  return (
    <form onSubmit={handleSubmit}>
      <input
        type="file"
        accept=".csv"
        onChange={(e) => setFile(e.target.files[0])}
      />
      <button type="submit" disabled={!file || loading}>
        {loading ? "Uploading..." : "Upload"}
      </button>
    </form>
  );
}
