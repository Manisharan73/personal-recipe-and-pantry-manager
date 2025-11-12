import React, { useEffect, useState } from "react";
import api from "../axiosConfig"; 
import "../styles/Home.css"; // Reuse existing styles

// NOTE: In a real app, userId should be retrieved from JWT/Context.
const userId = "93f5fed8-c2cd-4e70-a7a4-19b3a9506b25"; 

const Pantry = () => {
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
            const pantryRes = await api.get(`/pantry/${userId}`);
            setPantry(pantryRes.data);
            setMessage(""); // Clear message on successful fetch
        } catch (err) {
            console.error("Failed to fetch pantry:", err);
            setMessage("Failed to load pantry items.");
        }
    };

    useEffect(() => {
        fetchPantry();
    }, []);

    const handleBuyNewPantryItem = async (e) => {
        e.preventDefault();
        if (!newPantryItem.name || !newPantryItem.quantity || !newPantryItem.unit) {
            setMessage("Please fill in ingredient name, quantity, and unit.");
            return;
        }

        try {
            const res = await api.post("/buy-new-item", {
                user_id: userId,
                name: newPantryItem.name,
                quantity: parseFloat(newPantryItem.quantity),
                unit: newPantryItem.unit,
                expiration_date: newPantryItem.expiration_date || null,
            });
            setMessage(res.data.message);
            setNewPantryItem({ name: "", quantity: "", unit: "", expiration_date: "" });
            // Fetch new data (pantry updated)
            await fetchPantry(); 
        } catch (err) {
            console.error("Error buying new item:", err);
            setMessage(`Failed to add item to pantry: ${err.response?.data?.error || err.message}`);
        }
    };

    return (
        <>
            <h1>🧺 My Pantry</h1>
            {message && <p className="message-box">{message}</p>}

            {/* --- Buy New Ingredient Form --- */}
            <div className="add-recipe-section">
                <h2>🛍️ Add New Ingredient to Stock</h2>
                <form onSubmit={handleBuyNewPantryItem}>
                    <div className="ingredient-row">
                        {/* Ingredient Name */}
                        <input
                            type="text"
                            placeholder="Ingredient Name (e.g., Flour)"
                            aria-label="Ingredient Name"
                            value={newPantryItem.name}
                            onChange={(e) => setNewPantryItem({ ...newPantryItem, name: e.target.value })}
                            required
                        />
                        {/* Quantity */}
                        <input
                            type="number"
                            placeholder="Quantity"
                            aria-label="Quantity"
                            value={newPantryItem.quantity}
                            onChange={(e) => setNewPantryItem({ ...newPantryItem, quantity: e.target.value })}
                            required
                        />
                        {/* Unit */}
                        <input
                            type="text"
                            placeholder="Unit (e.g., kg, L, pcs)"
                            aria-label="Unit"
                            value={newPantryItem.unit}
                            onChange={(e) => setNewPantryItem({ ...newPantryItem, unit: e.target.value })}
                            required
                        />
                        {/* Expiration Date */}
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
            
            {/* --- Pantry Table --- */}
            <h2>📦 Current Pantry Stock</h2>
            <table>
                <thead>
                    <tr>
                        <th style={{ width: '30%' }}>Ingredient</th>
                        <th style={{ width: '20%' }}>Quantity</th>
                        <th style={{ width: '20%' }}>Unit</th>
                        <th style={{ width: '30%' }}>Expires</th>
                    </tr>
                </thead>
                <tbody>
                    {pantry.map((item) => (
                        <tr key={item.id}>
                            <td>{item.name}</td>
                            <td>{item.quantity}</td>
                            <td>{item.unit}</td>
                            <td>
                                {item.expiration_date 
                                    ? new Date(item.expiration_date).toLocaleDateString() // Format date for readability
                                    : 'N/A'
                                }
                            </td>
                        </tr>
                    ))}
                </tbody>
            </table>
        </>
    );
};

export default Pantry;