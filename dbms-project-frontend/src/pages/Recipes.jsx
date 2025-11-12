import React, { useEffect, useState } from "react";
import api from "../axiosConfig";
import "../styles/Home.css";

// NOTE: In a real app, userId should be retrieved from JWT/Context.
const userId = "93f5fed8-c2cd-4e70-a7a4-19b3a9506b25"; 

const Recipes = () => {
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
                api.get(`/recipes/${userId}`),
                api.get(`/recipe-ingredients/${userId}`),
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
        fetchData();
    }, []);

    const handleAddRecipe = async (e) => {
        e.preventDefault();
        try {
            await api.post("/recipe", {
                user_id: userId,
                title: newRecipe.title,
                description: newRecipe.description,
                ingredients: [],
            });
            setMessage("Recipe added successfully! Now add ingredients in the section below.");
            setNewRecipe({ title: "", description: "" });
            await fetchData(); // Refresh list
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
            await fetchData(); // Refresh list
        } catch (err) {
            console.error("Error adding ingredient:", err);
            setMessage(`Failed to add recipe ingredient: ${err.response?.data?.error || err.message}`);
        }
    };
    
    // Function to trigger regeneration on the Shopping List page
    const navigateToShoppingListAndRegenerate = () => {
        // Since we are decoupling, we just tell the user to navigate
        // A full solution would use state management or a context hook to signal regeneration
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


            {/* --- Recipes List --- */}
            <h2>🏠 My Saved Recipes</h2>
            <ul>
                {recipes.map((r) => (
                    <li key={r.id}>
                        <div>
                            <strong>{r.title}</strong>
                            <p style={{ margin: '0', fontSize: '0.9rem', color: '#666' }}>
                                {r.description}
                            </p>
                        </div>
                        <button
                            className="generate-btn"
                            onClick={navigateToShoppingListAndRegenerate}
                        >
                            Check Supplies 🛒
                        </button>
                    </li>
                ))}
            </ul>

            {/* --- Recipe Ingredients Table --- */}
            <h2>📋 Recipe Ingredients Detail</h2>
            <table>
                <thead>
                    <tr>
                        <th style={{ width: '30%' }}>Recipe</th>
                        <th style={{ width: '30%' }}>Ingredient</th>
                        <th style={{ width: '20%' }}>Quantity</th>
                        <th style={{ width: '20%' }}>Unit</th>
                    </tr>
                </thead>
                <tbody>
                    {recipeIngredients.map((ri) => (
                        <tr key={ri.id}>
                            <td>{ri.recipe_title}</td>
                            <td>{ri.ingredient_name}</td>
                            <td>{ri.quantity}</td>
                            <td>{ri.unit}</td>
                        </tr>
                    ))}
                </tbody>
            </table>
        </>
    );
};

export default Recipes;