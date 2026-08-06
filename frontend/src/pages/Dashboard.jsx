import { Link } from "react-router-dom";
import useAuth from "../hooks/useAuth";

export default function Dashboard() {
  const { user } = useAuth();

  return (
    <div className="dashboard-page">
      <section className="panel">
        <h2>Welcome{user ? `, ${user.name || user.email}` : ""}</h2>
        <p>Upload datasets, browse what you've got, or jump straight into analysis.</p>

        <div style={{ display: "flex", gap: "1rem", marginTop: "1.5rem" }}>
          <Link to="/analytics">
            <button>Upload / Manage Data</button>
          </Link>
          <Link to="/plot">
            <button>Compute & Plot</button>
          </Link>
        </div>
      </section>
    </div>
  );
}