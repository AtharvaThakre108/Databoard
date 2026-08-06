export default function DatasetList({
  datasets = [],
  onSelect,
  onDelete,
  selectedId,
}) {
  return (
    <div>
      {datasets.map((dataset) => (
        <div
          key={dataset.id}
          style={{
            display: "flex",
            justifyContent: "space-between",
            alignItems: "center",
            padding: "12px",
            marginBottom: "10px",
            border: "1px solid #334155",
            borderRadius: "8px",
            background:
              selectedId === dataset.id ? "#3b82f6" : "#1e293b",
            color: "#ffffff",
          }}
        >
          <span
            style={{
              cursor: "pointer",
              flex: 1,
              color: "#ffffff",
              fontWeight: "600",
              userSelect: "none",
            }}
            onClick={() => onSelect(dataset.id)}
          >
            {dataset.name}
          </span>

          {onDelete && (
            <button
              onClick={(e) => {
                e.stopPropagation();
                onDelete(dataset.id);
              }}
              style={{
                background: "#dc2626",
                color: "#fff",
                border: "none",
                padding: "6px 12px",
                borderRadius: "5px",
                cursor: "pointer",
              }}
            >
              Delete
            </button>
          )}
        </div>
      ))}
    </div>
  );
}