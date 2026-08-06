import { Link, useNavigate } from "react-router-dom";
import toast from "react-hot-toast";
import useAuth from "../hooks/useAuth";

export default function Navbar() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  const handleLogout = () => {
    logout();
    toast.success("Logged out");
    navigate("/login");
  };

  return (
    <nav className="navbar" style={{ display: "flex", alignItems: "center", padding: "0.75rem 1.5rem" }}>
      <Link className="brand" to="/" style={{ fontWeight: 700, marginRight: "2rem" }}>
        DataBoard
      </Link>

      {user && (
        <div className="nav-links" style={{ display: "flex", gap: "1.5rem", flex: 1 }}>
          <Link to="/analytics">Data</Link>
          <Link to="/plot">Plot</Link>
        </div>
      )}

      <div className="nav-right" style={{ display: "flex", alignItems: "center", gap: "1rem" }}>
        {user && <span className="nav-user">{user.name || user.email}</span>}
        {user && <button className="secondary-btn" onClick={handleLogout}>Logout</button>}
      </div>
    </nav>
  );
}