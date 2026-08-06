import { useState } from "react";
import { useNavigate, Link } from "react-router-dom";
import toast from "react-hot-toast";
import { registerUser } from "../api/auth";

export default function Register() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const navigate = useNavigate();

  const submit = async (e) => {
    e.preventDefault();
    try {
      await registerUser({ email, password });
      toast.success("Account created");
      navigate("/login");
    } catch (err) {
      const data = err.response?.data;

      const message = Array.isArray(data?.detail)
        ? data.detail[0]?.msg
        : data?.detail?.msg || data?.detail || err.message || "Registration failed";

      toast.error(message);
      console.log(err.response?.status);
      console.log(err.response?.data);
    }
  };

  return (
    <div className="auth-page">
      <form className="auth-card" onSubmit={submit}>
        <h1>Register</h1>
        <input
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          placeholder="Email"
        />
        <input
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          placeholder="Password"
          type="password"
        />
        <button type="submit">Register</button>
        <p>
          <Link to="/login">Already have an account?</Link>
        </p>
      </form>
    </div>
  );
}
