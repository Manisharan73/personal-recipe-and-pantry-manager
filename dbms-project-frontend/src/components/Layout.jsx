import React from 'react';
import { Outlet, NavLink } from 'react-router-dom';
import api from '../axiosConfig'; // Needed if you add a logout handler
import '../styles/Layout.css'; 

const Layout = () => {
    
  // NOTE: You should retrieve setIsAuthenticated from App.jsx via props or Context
  // For simplicity, we'll assume we handle the state in App.jsx

  const handleLogout = async () => {
      try {
          await api.post("/logout"); // Assuming a logout endpoint exists
          // NOTE: You would need to pass setIsAuthenticated from App
          // setIsAuthenticated(false);
          window.location.href = '/login-signup'; // Simple redirect for now
      } catch (err) {
          console.error("Logout failed:", err);
      }
  };

  return (
    <div className="app-layout">
      {/* Sidebar (Navigation) */}
      <aside className="sidebar">
        <div className="logo">
            <span role="img" aria-label="kitchen">🏠</span> My Kitchen
        </div>
        <nav className="nav-links">
          <NavLink to="/pantry" className={({ isActive }) => isActive ? 'nav-link active' : 'nav-link'}>
            🧺 My Pantry
          </NavLink>
          <NavLink to="/recipes" className={({ isActive }) => isActive ? 'nav-link active' : 'nav-link'}>
            📖 Recipes
          </NavLink>
          <NavLink to="/shopping-list" className={({ isActive }) => isActive ? 'nav-link active' : 'nav-link'}>
            🛒 Shopping List
          </NavLink>
        </nav>
        <button onClick={handleLogout} className="logout-btn">
            Logout
        </button>
      </aside>

      {/* Main Content Area - Renders the child route components */}
      <main className="content-area">
        <div className="content-wrapper">
            <Outlet /> 
        </div>
      </main>
    </div>
  );
};

export default Layout;