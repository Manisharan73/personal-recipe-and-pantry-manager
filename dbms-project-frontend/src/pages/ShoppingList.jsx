import React, { useEffect, useState } from "react";
import api from "../axiosConfig";
import "../styles/Home.css";

// NOTE: In a real app, userId should be retrieved from JWT/Context.
const userId = "93f5fed8-c2cd-4e70-a7a4-19b3a9506b25"; 

const ShoppingList = () => {
    const [shoppingList, setShoppingList] = useState([]);
    const [message, setMessage] = useState("");

    // 1. Regeneration logic separated
    const regenerateAndFetchShoppingList = async () => {
        setMessage("Generating shopping list...");
        try {
            // Force regeneration of the shopping list
            const res = await api.post(`/generate-shopping-list/${userId}`);
            
            // Fetch the newly generated list
            const shoppingRes = await api.get(`/shopping-list/${userId}`);
            setShoppingList(shoppingRes.data);
            setMessage(res.data.message || "Shopping list regenerated successfully.");
        } catch (err) {
            console.error("Error regenerating shopping list:", err);
            setMessage(`Failed to regenerate shopping list: ${err.response?.data?.error || err.message}`);
        }
    };
    
    useEffect(() => {
        regenerateAndFetchShoppingList(); // Fetch and regenerate on load
    }, []);

    const handleBuyShoppingItem = async (itemId) => {
        try {
            // Note: This endpoint should handle both updating the pantry and removing the item from the list
            const res = await api.post(`/buy-item/${userId}/${itemId}`);
            setMessage(res.data.message);
            
            // Optimistic update for faster UI response:
            setShoppingList(prevList => prevList.filter(item => item.id !== itemId));

            // Small delay to show optimistic update before a full refresh (optional, but good UX)
            setTimeout(() => {
                regenerateAndFetchShoppingList(); 
            }, 500);

        } catch (err) {
            console.error("Error buying item:", err);
            setMessage(`Failed to buy item: ${err.response?.data?.error || err.message}`);
        }
    };

    return (
        <>
            <h1>🛒 Shopping List</h1>
            {message && <p className="message-box">{message}</p>}

            {/* --- List Header and Regenerate Button --- */}
            <h2 style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                Items Needed 
                <button 
                    onClick={regenerateAndFetchShoppingList} 
                    className="generate-btn"
                    style={{ margin: 0 }} // Override any default margin from h2 styling
                >
                    🔁 Regenerate List
                </button>
            </h2>

            {/* --- Shopping List Table --- */}
            <table>
                <thead>
                    <tr>
                        <th style={{ width: '40%' }}>Ingredient</th>
                        <th style={{ width: '20%' }}>Quantity</th>
                        <th style={{ width: '20%' }}>Unit</th>
                        <th style={{ width: '20%', textAlign: 'center' }}>Action</th> 
                    </tr>
                </thead>
                <tbody>
                    {shoppingList.length > 0 ? (
                        shoppingList.map((item) => (
                            <tr key={item.id}>
                                <td>{item.ingredient_name}</td>
                                <td>{item.quantity}</td>
                                <td>{item.unit}</td>
                                <td style={{ textAlign: 'center' }}>
                                    <button
                                        className="buy-btn"
                                        onClick={() => handleBuyShoppingItem(item.id)}
                                    >
                                        Buy ✅
                                    </button>
                                </td>
                            </tr>
                        ))
                    ) : (
                        <tr>
                            <td colSpan="4" style={{ textAlign: 'center', padding: '20px', fontStyle: 'italic', color: '#666' }}>
                                🎉 Your shopping list is empty! Ready to cook!
                            </td>
                        </tr>
                    )}
                </tbody>
            </table>
        </>
    );
};

export default ShoppingList;