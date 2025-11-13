import { useState } from "react";
import api from "../axiosConfig";
import { useNavigate } from "react-router-dom";
import "../styles/Login_SignUp.css";

const Login_SignUp = ({ setIsAuthenticated, setUserId }) => {
  const [activeTab, setActiveTab] = useState("login");
  const [formData, setFormData] = useState({ username: "", email: "", password: "" });
  const navigate = useNavigate();

  const handleChange = (e) =>
    setFormData({ ...formData, [e.target.name]: e.target.value });

  const handleSignup = async (e) => {
    e.preventDefault();
    try {
      const res = await api.post("/signup", formData);
      alert(res.data.message);
      setIsAuthenticated(true);
      setFormData({ username: "", email: "", password: "" });
      navigate("/");
    } catch (err) {
      alert(err.response?.data?.message || "Signup failed");
    }
  };

  const handleLogin = async (e) => {
    e.preventDefault();
    try {
      const res = await api.post("/login", {
        email: formData.email,
        password: formData.password,
      });
      alert(res.data.message);
      setIsAuthenticated(true);
      setUserId(res.data.user_id);
      setFormData({ username: "", email: "", password: "" });
      navigate("/");
    } catch (err) {
      alert(err.response?.data?.message || "Login failed");
    }
  };

  return (
    <div className="login-signup-wrapper">
      <div className="form-container">
        <h1>🍳 Recipe & Pantry Manager</h1>

        <div className="tabs">
          <button
            className={`tab-label ${activeTab === "login" ? "active" : ""}`}
            onClick={() => setActiveTab("login")}
          >
            Login
          </button>
          <button
            className={`tab-label ${activeTab === "signup" ? "active" : ""}`}
            onClick={() => setActiveTab("signup")}
          >
            Sign Up
          </button>
        </div>

        <div className="slider">
          <div className={`forms ${activeTab}`}>
            <form className="auth-form" onSubmit={handleLogin}>
              <label>Email</label>
              <input
                name="email"
                type="email"
                placeholder="Enter your email"
                required
                onChange={handleChange}
                value={formData.email}
              />
              <label>Password</label>
              <input
                name="password"
                type="password"
                placeholder="Enter your password"
                required
                onChange={handleChange}
                value={formData.password}
              />
              <button type="submit" className="btn">
                Login
              </button>
            </form>

            <form className="auth-form" onSubmit={handleSignup}>
              <label>Username</label>
              <input
                name="username"
                type="text"
                placeholder="Enter your username"
                required
                onChange={handleChange}
                value={formData.username}
              />
              <label>Email</label>
              <input
                name="email"
                type="email"
                placeholder="Enter your email"
                required
                onChange={handleChange}
                value={formData.email}
              />
              <label>Password</label>
              <input
                name="password"
                type="password"
                placeholder="Enter your password"
                required
                onChange={handleChange}
                value={formData.password}
              />
              <button type="submit" className="btn">
                Sign Up
              </button>
            </form>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Login_SignUp;