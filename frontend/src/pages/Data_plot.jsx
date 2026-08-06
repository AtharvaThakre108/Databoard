import { useEffect, useState } from "react";
import toast from "react-hot-toast";
import {
  getDatasets,
  previewDataset,
  computeDataset,
  plotDataset,
} from "../api/dataset";

import DatasetList from "../components/DatasetList";
import ReactECharts from "echarts-for-react";

export default function DataPlot() {
  const [datasets, setDatasets] = useState([]);
  const [selectedId, setSelectedId] = useState(null);
  const [columns, setColumns] = useState([]);

  const [column, setColumn] = useState("");
  const [operation, setOperation] = useState("sum");
  const [computeResult, setComputeResult] = useState(null);

  const [xColumn, setXColumn] = useState("");
  const [yColumn, setYColumn] = useState("");
  const [chartType, setChartType] = useState("scatter");
  const [plotData, setPlotData] = useState([]);

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
    setColumn("");
    setComputeResult(null);
    setXColumn("");
    setYColumn("");
    setPlotData([]);

    try {
      // Reuses the preview endpoint purely to get the column list --
      // no need for a separate "columns only" route.
      const res = await previewDataset(id);
      setColumns(res.data.columns);
    } catch (err) {
      console.error(err);
      toast.error("Failed to load dataset columns");
    }
  };

  const handleCompute = async () => {
    if (!selectedId) {
      toast.error("Select a dataset first");
      return;
    }
    if (!column) {
      toast.error("Select a column");
      return;
    }

    try {
      const res = await computeDataset(selectedId, { column, operation });
      setComputeResult(res.data);
    } catch (err) {
      console.error(err);
      toast.error(err.response?.data?.detail || "Compute failed");
    }
  };

  const handlePlot = async () => {
    if (!selectedId) {
      toast.error("Select a dataset");
      return;
    }
    if (!xColumn || !yColumn) {
      toast.error("Select two columns");
      return;
    }

    try {
      const res = await plotDataset(selectedId, { col1: xColumn, col2: yColumn });
      setPlotData(res.data.points);
    } catch (err) {
      console.error(err);
      toast.error(err.response?.data?.detail || "Plot failed");
    }
  };

  const chartOption = {
    tooltip: {},
    xAxis: { type: "value", name: xColumn },
    yAxis: { type: "value", name: yColumn },
    series: [
      {
        type: chartType,
        data: plotData.map((p) => [p.x, p.y]),
      },
    ],
  };

  useEffect(() => {
    load();
  }, []);

  return (
    <div className="dashboard-page">
      <div className="dashboard-grid">
        <section className="panel">
          <h2>Choose a Dataset</h2>
          <DatasetList
            datasets={datasets}
            onSelect={handleDatasetSelect}
            selectedId={selectedId}
          />
        </section>

        {selectedId && (
          <section className="panel">
            <h2>Compute Statistics</h2>

            <select value={column} onChange={(e) => setColumn(e.target.value)}>
              <option value="">Select Column</option>
              {columns.map((col) => (
                <option key={col} value={col}>
                  {col}
                </option>
              ))}
            </select>

            <select value={operation} onChange={(e) => setOperation(e.target.value)}>
              <option value="sum">Sum</option>
              <option value="min">Minimum</option>
              <option value="max">Maximum</option>
            </select>

            <button onClick={handleCompute}>Compute</button>

            {computeResult && (
              <div
                style={{
                  marginTop: "20px",
                  padding: "15px",
                  border: "1px solid #444",
                  borderRadius: "6px",
                }}
              >
                <h3>Result</h3>
                <p><strong>Column:</strong> {computeResult.column}</p>
                <p><strong>Operation:</strong> {computeResult.operation}</p>
                <p><strong>Result:</strong> {computeResult.result}</p>
                <p><strong>Values Considered:</strong> {computeResult.values_considered}</p>
                <p><strong>Values Skipped:</strong> {computeResult.values_skipped}</p>
              </div>
            )}

            <hr />
            <h2>Plot</h2>

            <select value={xColumn} onChange={(e) => setXColumn(e.target.value)}>
              <option value="">X Column</option>
              {columns.map((col) => (
                <option key={col}>{col}</option>
              ))}
            </select>

            <select value={yColumn} onChange={(e) => setYColumn(e.target.value)}>
              <option value="">Y Column</option>
              {columns.map((col) => (
                <option key={col}>{col}</option>
              ))}
            </select>

            <select value={chartType} onChange={(e) => setChartType(e.target.value)}>
              <option value="scatter">Scatter</option>
              <option value="line">Line</option>
              <option value="bar">Bar</option>
            </select>

            <button onClick={handlePlot}>Plot</button>

            {plotData.length > 0 && (
              <ReactECharts option={chartOption} style={{ height: 450, marginTop: 20 }} />
            )}
          </section>
        )}
      </div>
    </div>
  );
}