import { useEffect, useState } from "react";
import { BrowserRouter as Router, Routes, Route, Navigate } from "react-router-dom";
import api from "./axiosConfig"; 
// New Imports
import Login_SignUp from "./pages/Login_SignUp";
import Layout from "./components/Layout";
import Pantry from "./pages/Pantry";
import Recipes from "./pages/Recipes";
import ShoppingList from "./pages/ShoppingList";

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
        {/* 1. Login/Signup Route (Unauthenticated) */}
        <Route
          path="/login-signup"
          element={<Login_SignUp setIsAuthenticated={setIsAuthenticated} />}
        />

        {/* 2. Protected Routes (Wrapped in Layout) */}
        <Route 
          path="/" 
          element={isAuthenticated ? <Layout /> : <Navigate to="/login-signup" />}
        >
          {/* Default route redirects to Pantry */}
          <Route index element={<Navigate to="/pantry" replace />} /> 
          
          {/* Feature Routes */}
          <Route path="pantry" element={<Pantry />} />
          <Route path="recipes" element={<Recipes />} />
          <Route path="shopping-list" element={<ShoppingList />} />
        
          {/* Catch-all inside protected section */}
          <Route path="*" element={<Navigate to="/pantry" replace />} />
        </Route>

        {/* 3. Catch-all for unauthenticated users */}
        <Route path="*" element={<Navigate to="/login-signup" />} />
      </Routes>
    </Router>
  );
}

export default App;