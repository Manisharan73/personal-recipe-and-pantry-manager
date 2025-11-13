import { useEffect, useState } from "react";
import { BrowserRouter as Router, Routes, Route, Navigate } from "react-router-dom";
import api from "./axiosConfig"; 
import Login_SignUp from "./pages/Login_SignUp";
import Layout from "./components/Layout";
import Pantry from "./pages/Pantry";
import Recipes from "./pages/Recipes";
import ShoppingList from "./pages/ShoppingList";

function App() {
    const [isAuthenticated, setIsAuthenticated] = useState(null);
    const [userId, setUserId] = useState(null); 

    const [themeMode, setThemeMode] = useState(
        localStorage.getItem('themeMode') || 'light'
    );

    const toggleTheme = () => {
        setThemeMode(prevMode => {
            const newMode = prevMode === 'light' ? 'dark' : 'light';
            localStorage.setItem('themeMode', newMode);
            return newMode;
        });
    };

    useEffect(() => {
        const checkAuth = async () => {
            try {
                const res = await api.get("/verify-token");
                setIsAuthenticated(res.data.logged_in);
                if (res.data.logged_in) {
                    setUserId(res.data.user_id); 
                }
            } catch (err) {
                console.error("Auth check failed:", err);
                setIsAuthenticated(false);
                setUserId(null);
            }
        };
        checkAuth();
    }, []);

    if (isAuthenticated === null) return <p>Loading...</p>;

    return (
        <Router>
            <div className={`app-container ${themeMode}`}>
                <Routes>
                    <Route
                        path="/login-signup"
                        element={<Login_SignUp setIsAuthenticated={setIsAuthenticated} setUserId={setUserId} />}
                    />

                    <Route 
                        path="/" 
                        element={
                            isAuthenticated 
                                ? <Layout 
                                    setIsAuthenticated={setIsAuthenticated} 
                                    setUserId={setUserId} 
                                    themeMode={themeMode} 
                                    toggleTheme={toggleTheme}
                                  /> 
                                : <Navigate to="/login-signup" />
                        }
                    >
                        <Route index element={<Navigate to="/pantry" replace />} /> 

                        <Route path="pantry" element={<Pantry userId={userId} />} />
                        <Route path="recipes" element={<Recipes userId={userId} />} />
                        <Route path="shopping-list" element={<ShoppingList userId={userId} />} />

                        <Route path="*" element={<Navigate to="/pantry" replace />} />
                    </Route>

                    <Route path="*" element={<Navigate to="/login-signup" />} />
                </Routes>
            </div>
        </Router>
    );
}

export default App;