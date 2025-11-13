import React, { useEffect, useState } from "react";
import api from "../axiosConfig"; 
import "../styles/Home.css"; 

const Pantry = ({ userId }) => { // Accept userId as prop
    const [pantry, setPantry] = useState([]);
    const [message, setMessage] = useState("");
    const [newPantryItem, setNewPantryItem] = useState({
        name: "",
        quantity: "",
        unit: "",
        expiration_date: "", 
    });

    const fetchPantry = async () => {
        try {
            // Note: API call is now simply /pantry as user_id is handled by decorator
            const pantryRes = await api.get(`/pantry`); 
            setPantry(pantryRes.data);
            setMessage(""); 
        } catch (err) {
            console.error("Failed to fetch pantry:", err);
            setMessage("Failed to load pantry items.");
        }
    };

    const isExpiringSoon = (expirationDate) => {
        if (!expirationDate) return false;
        const today = new Date();
        const expiration = new Date(expirationDate);
        const diffDays = (expiration - today) / (1000 * 60 * 60 * 24);
        // Item is expiring if it's not past today and is within the next 7 days
        return diffDays > 0 && diffDays <= 7;
    };

    useEffect(() => {
        if (userId) { 
            fetchPantry();
        }
    }, [userId]);

    const handleBuyNewPantryItem = async (e) => {
        e.preventDefault();
        if (!newPantryItem.name || !newPantryItem.quantity || !newPantryItem.unit) {
            setMessage("Please fill in ingredient name, quantity, and unit.");
            return;
        }

        try {
            const res = await api.post("/buy-new-item", {
                name: newPantryItem.name,
                // Ensure quantity is parsed as float before sending
                quantity: parseFloat(newPantryItem.quantity),
                unit: newPantryItem.unit,
                expiration_date: newPantryItem.expiration_date || null,
            });
            setMessage(res.data.message);
            setNewPantryItem({ name: "", quantity: "", unit: "", expiration_date: "" });
            await fetchPantry();
        } catch (err) {
            console.error("Error buying new item:", err);
            setMessage(`Failed to add item to pantry: ${err.response?.data?.error || err.message}`);
        }
    };
    
    // --- NEW DELETE HANDLER ---
    const handleDeletePantryItem = async (itemId, itemName) => {
        if (!window.confirm(`Are you sure you want to delete ${itemName} from your pantry?`)) {
            return;
        }
        try {
            await api.delete(`/pantry/${itemId}`);
            setMessage(`${itemName} successfully deleted from pantry.`);
            // Optimistic update: remove item from state
            setPantry(prevPantry => prevPantry.filter(item => item.id !== itemId));
        } catch (err) {
            console.error("Error deleting item:", err);
            setMessage(`Failed to delete item: ${err.response?.data?.error || err.message}`);
        }
    };
    // --- END NEW DELETE HANDLER ---

    return (
        <>
            <h1>🧺 My Pantry</h1>
            {message && <p className="message-box">{message}</p>}

            {/* --- Buy New Ingredient Form --- */}
            <div className="add-recipe-section">
                <h2>🛍️ Add New Ingredient to Stock</h2>
                <form onSubmit={handleBuyNewPantryItem}>
                    <div className="ingredient-row">
                        <input
                            type="text"
                            placeholder="Ingredient Name (e.g., Flour)"
                            aria-label="Ingredient Name"
                            value={newPantryItem.name}
                            onChange={(e) => setNewPantryItem({ ...newPantryItem, name: e.target.value })}
                            required
                        />
                        <input
                            type="number"
                            placeholder="Quantity"
                            aria-label="Quantity"
                            value={newPantryItem.quantity}
                            onChange={(e) => setNewPantryItem({ ...newPantryItem, quantity: e.target.value })}
                            required
                        />
                        <input
                            type="text"
                            placeholder="Unit (e.g., kg, L, pcs)"
                            aria-label="Unit"
                            value={newPantryItem.unit}
                            onChange={(e) => setNewPantryItem({ ...newPantryItem, unit: e.target.value })}
                            required
                        />
                        <input
                            type="date"
                            title="Expiration Date (optional)"
                            aria-label="Expiration Date"
                            value={newPantryItem.expiration_date}
                            onChange={(e) => setNewPantryItem({ ...newPantryItem, expiration_date: e.target.value })}
                        />
                        <button type="submit" className="buy-new-btn">
                            Add to Pantry
                        </button>
                    </div>
                </form>
            </div>
            
            {/* --- Pantry Stock Card Display (MODIFIED) --- */}
            <h2>📦 Current Pantry Stock</h2>
            <div className="card-grid">
                {pantry.length > 0 ? (
                    pantry.map((item) => (
                        <div 
                            key={item.id} 
                            className={`card ${isExpiringSoon(item.expiration_date) ? 'expiring' : ''}`}
                        >
                            <p className="card-title">{item.name}</p>
                            <p className="card-detail">
                                <strong>Quantity:</strong> {item.quantity} {item.unit}
                            </p>
                            <p className="card-detail" style={{ color: isExpiringSoon(item.expiration_date) ? '#e67e22' : '#555' }}>
                                <strong>Expires:</strong> {item.expiration_date 
                                    ? new Date(item.expiration_date).toLocaleDateString()
                                    : 'N/A'
                                }
                                {isExpiringSoon(item.expiration_date) && ' ⚠️ Soon!'}
                            </p>
                            <div className="card-actions">
                                <button 
                                    className="delete-btn"
                                    onClick={() => handleDeletePantryItem(item.id, item.name)}
                                >
                                    Delete 🗑️
                                </button>
                            </div>
                        </div>
                    ))
                ) : (
                    <p style={{ gridColumn: '1 / -1', textAlign: 'center', fontStyle: 'italic' }}>
                        Your pantry is empty. Time to go shopping!
                    </p>
                )}
            </div>
        </>
    );
};

export default Pantry;