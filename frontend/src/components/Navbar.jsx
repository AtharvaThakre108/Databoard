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
    <nav className="navbar">
      <Link className="brand" to="/">DataApp</Link>
      <div className="nav-right">
        {user && <span className="nav-user">{user.name || user.email}</span>}
        {user && <button className="secondary-btn" onClick={handleLogout}>Logout</button>}
      </div>
    </nav>
  );
}
