import { useEffect, useState } from "react";
import toast from "react-hot-toast";
import { getDatasets, previewDataset, deleteDataset } from "../api/dataset";

import UploadForm from "../components/UploadForm";
import DatasetList from "../components/DatasetList";

export default function DataAnalytics() {
  const [datasets, setDatasets] = useState([]);
  const [preview, setPreview] = useState(null);
  const [selectedId, setSelectedId] = useState(null);

  const load = async () => {
    try {
      const res = await getDatasets();
      setDatasets(res.data.items);
    } catch {
      toast.error("Failed to load datasets");
    }
  };

  const handleDatasetSelect = async (id) => {
    setSelectedId(id);

    try {
      const res = await previewDataset(id);
      setPreview(res.data);
    } catch (err) {
      console.error(err);
      toast.error("Failed to load preview");
    }
  };

  const handleDelete = async (id) => {
    if (!window.confirm("Delete this dataset permanently?")) {
      return;
    }

    try {
      await deleteDataset(id);
      toast.success("Dataset deleted");

      if (selectedId === id) {
        setSelectedId(null);
        setPreview(null);
      }

      load();
    } catch {
      toast.error("Delete failed");
    }
  };

  useEffect(() => {
    load();
  }, []);

  return (
    <div className="dashboard-page">
      <div className="dashboard-grid">
        <section className="panel">
          <h2>Upload Dataset</h2>
          <UploadForm onUploaded={load} />
        </section>

        <section className="panel">
          <h2>Your Datasets</h2>

          <DatasetList
            datasets={datasets}
            onSelect={handleDatasetSelect}
            onDelete={handleDelete}
            selectedId={selectedId}
          />

          {preview && (
            <>
              <hr />
              <h2>Dataset Preview</h2>

              <table border="1" cellPadding="5">
                <thead>
                  <tr>
                    {preview.columns.map((col) => (
                      <th key={col}>{col}</th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {preview.rows.map((row, index) => (
                    <tr key={index}>
                      {preview.columns.map((col) => (
                        <td key={col}>{row[col]}</td>
                      ))}
                    </tr>
                  ))}
                </tbody>
              </table>
            </>
          )}
        </section>
      </div>
    </div>
  );
}