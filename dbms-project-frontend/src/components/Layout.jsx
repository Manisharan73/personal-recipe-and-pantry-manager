// Layout.jsx

import React from 'react';
import { Outlet, NavLink, useNavigate } from 'react-router-dom';
import api from '../axiosConfig'; 
import '../styles/Layout.css'; 

// MODIFIED: Accept themeMode and toggleTheme as props
const Layout = ({ setIsAuthenticated, setUserId, themeMode, toggleTheme }) => { 
    const navigate = useNavigate();

    const handleLogout = async () => {
        try {
            await api.post("/logout");
            // Clean state and redirect
            setIsAuthenticated(false);
            setUserId(null); 
            navigate('/login-signup'); 
        } catch (err) {
            console.error("Logout failed:", err);
            // Even if API call fails, clear local state and force redirect
            setIsAuthenticated(false);
            setUserId(null);
            navigate('/login-signup'); 
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
                
                {/* NEW: Theme Toggle */}
                <button onClick={toggleTheme} className="theme-toggle-btn">
                    {themeMode === 'light' ? 'Dark Mode 🌙' : 'Light Mode ☀️'}
                </button>
                {/* END NEW */}
                
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