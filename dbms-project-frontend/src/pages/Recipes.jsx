import React, { useEffect, useState } from "react";
import api from "../axiosConfig";
import "../styles/Home.css";

const Recipes = ({ userId }) => { 
    const [recipes, setRecipes] = useState([]);
    const [recipeIngredients, setRecipeIngredients] = useState([]);
    const [allIngredients, setAllIngredients] = useState([]); 
    const [message, setMessage] = useState("");

    const [newRecipe, setNewRecipe] = useState({ title: "", description: "" });
    const [newRecipeIng, setNewRecipeIng] = useState({
        recipe_id: "",
        ingredient_id: "",
        quantity: "",
        unit: "",
    });

    const fetchData = async () => {
        try {
            const [recipeRes, recipeIngRes, allIngRes] = await Promise.all([
                api.get(`/recipes`),
                api.get(`/recipe-ingredients`),
                api.get(`/ingredients`), 
            ]);

            setRecipes(recipeRes.data);
            setRecipeIngredients(recipeIngRes.data);
            setAllIngredients(allIngRes.data); 
            setMessage("");
        } catch (err) {
            console.error("Failed to fetch recipe data:", err);
            setMessage("Failed to load recipes and ingredients.");
        }
    };

    useEffect(() => {
        if (userId) {
            fetchData();
        }
    }, [userId]);

    const handleAddRecipe = async (e) => {
        e.preventDefault();
        try {
            await api.post("/recipe", {
                title: newRecipe.title,
                description: newRecipe.description,
                ingredients: [],
            });
            setMessage("Recipe added successfully! Now add ingredients in the section below.");
            setNewRecipe({ title: "", description: "" });
            await fetchData();
        } catch (err) {
            console.error("Error adding recipe:", err);
            setMessage(`Failed to add recipe: ${err.response?.data?.error || err.message}`);
        }
    };

    const handleAddRecipeIngredient = async (e) => {
        e.preventDefault();
        try {
            await api.post("/recipe-ingredient", {
                recipe_id: newRecipeIng.recipe_id,
                ingredient_id: newRecipeIng.ingredient_id,
                quantity: newRecipeIng.quantity,
                unit: newRecipeIng.unit,
            });
            setMessage("Ingredient added to recipe successfully! (Shopping list needs regeneration to update.)");
            setNewRecipeIng({
                recipe_id: newRecipeIng.recipe_id, 
                ingredient_id: "",
                quantity: "",
                unit: "",
            });
            await fetchData();
        } catch (err) {
            console.error("Error adding ingredient:", err);
            setMessage(`Failed to add recipe ingredient: ${err.response?.data?.error || err.message}`);
        }
    };
    
    // --- NEW DELETE HANDLER ---
    const handleDeleteRecipe = async (recipeId, recipeTitle) => {
        if (!window.confirm(`Are you sure you want to delete the recipe: ${recipeTitle}? This will also remove all its ingredients.`)) {
            return;
        }
        try {
            const res = await api.delete(`/recipe/${recipeId}`);
            setMessage(res.data.message);
            // Re-fetch all data to update both recipe list and recipe ingredients detail
            await fetchData();
        } catch (err) {
            console.error("Error deleting recipe:", err);
            setMessage(`Failed to delete recipe: ${err.response?.data?.error || err.message}`);
        }
    };
    // --- END NEW DELETE HANDLER ---
    
    const navigateToShoppingListAndRegenerate = () => {
        setMessage("Recipe modification noted! Please navigate to the Shopping List and click 'Regenerate List' to update supplies needed.");
    };


    return (
        <>
            <h1>📖 My Recipes</h1>
            {message && <p className="message-box">{message}</p>}

            {/* --- Create New Recipe Section --- */}
            <div className="add-recipe-section">
                <h2>📝 Create New Recipe</h2>
                <form onSubmit={handleAddRecipe}>
                    <input
                        type="text"
                        placeholder="e.g. Grandma's Famous Chili"
                        aria-label="Recipe Name"
                        value={newRecipe.title}
                        onChange={(e) =>
                            setNewRecipe({ ...newRecipe, title: e.target.value })
                        }
                        required
                    />
                    <input
                        type="text"
                        placeholder="e.g. A hearty, spicy meal for cold evenings."
                        aria-label="Short Description"
                        value={newRecipe.description}
                        onChange={(e) =>
                            setNewRecipe({ ...newRecipe, description: e.target.value })
                        }
                    />
                    <button type="submit" className="add-recipe-btn">
                        Create Recipe
                    </button>
                </form>
            </div>

            {/* --- Add Ingredient to Existing Recipe Section --- */}
            <div className="add-recipe-section">
                <h2>➕ Add Ingredient to Recipe</h2>
                <form onSubmit={handleAddRecipeIngredient}>
                    <div className="ingredient-row">
                        {/* Select Recipe */}
                        <select
                            value={newRecipeIng.recipe_id}
                            onChange={(e) =>
                                setNewRecipeIng({ ...newRecipeIng, recipe_id: e.target.value, })
                            }
                            required
                            aria-label="Select Recipe"
                        >
                            <option value="">Select Recipe</option>
                            {recipes.map((r) => (
                                <option key={r.id} value={r.id}>
                                    {r.title}
                                </option>
                            ))}
                        </select>

                        {/* Select Ingredient */}
                        <select
                            value={newRecipeIng.ingredient_id}
                            onChange={(e) =>
                                setNewRecipeIng({ ...newRecipeIng, ingredient_id: e.target.value, })
                            }
                            required
                            aria-label="Select Ingredient"
                        >
                            <option value="">Select Ingredient</option>
                            {allIngredients.map((ing) => (
                                <option key={ing.id} value={ing.id}>
                                    {ing.name}
                                </option>
                            ))}
                        </select>

                        {/* Quantity */}
                        <input
                            type="number"
                            placeholder="Quantity"
                            value={newRecipeIng.quantity}
                            onChange={(e) =>
                                setNewRecipeIng({ ...newRecipeIng, quantity: e.target.value, })
                            }
                            required
                            aria-label="Quantity"
                        />
                        {/* Unit */}
                        <input
                            type="text"
                            placeholder="Unit (e.g., g, ml, tsp)"
                            value={newRecipeIng.unit}
                            onChange={(e) =>
                                setNewRecipeIng({ ...newRecipeIng, unit: e.target.value, })
                            }
                            required
                            aria-label="Unit"
                        />
                        <button type="submit" className="add-recipe-btn">
                            Add Ingredient
                        </button>
                    </div>
                </form>
            </div>


            {/* --- Recipes List (MODIFIED) --- */}
            <h2>🏠 My Saved Recipes</h2>
            <ul>
                {recipes.map((r) => (
                    <li key={r.id}>
                        <div style={{ flexGrow: 1 }}>
                            <strong>{r.title}</strong>
                            <p style={{ margin: '0', fontSize: '0.9rem', color: '#666' }}>
                                {r.description}
                            </p>
                        </div>
                        <div style={{ display: 'flex', gap: '10px' }}>
                            <button
                                className="generate-btn"
                                onClick={navigateToShoppingListAndRegenerate}
                            >
                                Check Supplies 🛒
                            </button>
                            <button
                                className="delete-btn"
                                onClick={() => handleDeleteRecipe(r.id, r.title)}
                            >
                                Delete 🗑️
                            </button>
                        </div>
                    </li>
                ))}
            </ul>

            {/* --- Recipe Ingredients Detail Card Display --- */}
            <h2>📋 Recipe Ingredients Detail</h2>
            <div className="card-grid">
                {recipeIngredients.length > 0 ? (
                    recipeIngredients.map((ri) => (
                        <div key={ri.id} className="card">
                            <p className="card-title">{ri.ingredient_name}</p>
                            <p className="card-detail"><strong>For Recipe:</strong> {ri.recipe_title}</p>
                            <p className="card-detail"><strong>Quantity:</strong> {ri.quantity} {ri.unit}</p>
                        </div>
                    ))
                ) : (
                    <p style={{ gridColumn: '1 / -1', textAlign: 'center', fontStyle: 'italic' }}>
                        Add some ingredients to your recipes above!
                    </p>
                )}
            </div>
        </>
    );
};

export default Recipes;