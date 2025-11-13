import React, { useEffect, useState } from "react";
import api from "../axiosConfig";
import "../styles/Home.css";

const ShoppingList = ({ userId }) => {
    const [shoppingList, setShoppingList] = useState([]);
    const [message, setMessage] = useState("");

    const regenerateAndFetchShoppingList = async () => {
        setMessage("Generating shopping list...");
        try {
            const res = await api.post(`/generate-shopping-list`);

            const shoppingRes = await api.get(`/shopping-list`);
            setShoppingList(shoppingRes.data);
            setMessage(res.data.message || "Shopping list regenerated successfully.");
        } catch (err) {
            console.error("Error regenerating shopping list:", err);
            setMessage(`Failed to regenerate shopping list: ${err.response?.data?.error || err.message}`);
        }
    };

    useEffect(() => {
        if (userId) {
            regenerateAndFetchShoppingList();
        }
    }, [userId]);

    const handleBuyShoppingItem = async (itemId) => {
        try {
            const res = await api.post(`/buy-item/${itemId}`);
            setMessage(res.data.message);

            setShoppingList(prevList => prevList.filter(item => item.id !== itemId));

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
            <div className="sl-wrapper">
                <h1>🛒 Shopping List</h1>
                {message && <p className="message-box">{message}</p>}

                <h2 style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    Items Needed
                    <button
                        onClick={regenerateAndFetchShoppingList}
                        className="generate-btn"
                        style={{ margin: 0 }}
                    >
                        🔁 Regenerate List
                    </button>
                </h2>

                <div className="card-grid">
                    {shoppingList.length > 0 ? (
                        shoppingList.map((item) => (
                            <div key={item.id} className="card">
                                <div className="card-content">
                                    <p className="card-title">{item.ingredient_name}</p>
                                    <p className="card-detail"><strong>Quantity:</strong> {item.quantity} {item.unit}</p>
                                </div>
                                <div className="card-actions">
                                    <button
                                        className="buy-btn"
                                        onClick={() => handleBuyShoppingItem(item.id)}
                                    >
                                        Buy ✅
                                    </button>
                                </div>
                            </div>
                        ))
                    ) : (
                        <p style={{ gridColumn: '1 / -1', textAlign: 'center', padding: '20px', fontStyle: 'italic', color: '#666' }}>
                            🎉 Your shopping list is empty! Ready to cook!
                        </p>
                    )}
                </div>
            </div>
        </>
    );
};

export default ShoppingList;