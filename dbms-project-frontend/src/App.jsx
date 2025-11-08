import { useEffect, useState } from "react";
import { BrowserRouter as Router, Routes, Route, Navigate } from "react-router-dom";
import api from "./axiosConfig"; 
import Home from "./pages/Home";
import Login_SignUp from "./pages/Login_SignUp";

function App() {
  const [isAuthenticated, setIsAuthenticated] = useState(null);

  useEffect(() => {
    const checkAuth = async () => {
      try {
        const res = await api.get("/verify-token");
        setIsAuthenticated(res.data.logged_in);
      } catch (err) {
        console.error("Auth check failed:", err);
        setIsAuthenticated(false);
      }
    };
    checkAuth();
  }, []);

  if (isAuthenticated === null) return <p>Loading...</p>;

  return (
    <Router>
      <Routes>
        <Route path="/" element={isAuthenticated ? <Home /> : <Navigate to="/login-signup" />} />
        <Route
          path="/login-signup"
          element={<Login_SignUp setIsAuthenticated={setIsAuthenticated} />}
        />
        <Route path="*" element={isAuthenticated ? <Navigate to="/"/> : <Navigate to="/login-signup"/>}/>
      </Routes>
    </Router>
  );
}

export default App;
