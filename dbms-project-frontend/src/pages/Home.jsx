import React, { useEffect, useState } from "react";
import "../styles/Home.css";
import api from "../axiosConfig";

const Home = () => {
  // NOTE: In a real app, userId should be retrieved from JWT or context.
  const userId = "93f5fed8-c2cd-4e70-a7a4-19b3a9506b25";

  const [pantry, setPantry] = useState([]);
  const [recipes, setRecipes] = useState([]);
  const [recipeIngredients, setRecipeIngredients] = useState([]);
  const [shoppingList, setShoppingList] = useState([]);
  const [allIngredients, setAllIngredients] = useState([]); // NEW STATE for all DB ingredients
  const [message, setMessage] = useState("");

  const [newRecipe, setNewRecipe] = useState({ title: "", description: "" });
  const [newRecipeIng, setNewRecipeIng] = useState({
    recipe_id: "",
    ingredient_id: "",
    quantity: "",
    unit: "",
  });
  const [newPantryItem, setNewPantryItem] = useState({
    name: "",
    quantity: "",
    unit: "",
    expiration_date: "", // ISO format: YYYY-MM-DD
  });

  const fetchData = async () => {
    try {
      const [pantryRes, recipeRes, recipeIngRes, shoppingRes, allIngRes] = await Promise.all([
        api.get(`/pantry/${userId}`),
        api.get(`/recipes/${userId}`),
        api.get(`/recipe-ingredients/${userId}`),
        api.get(`/shopping-list/${userId}`),
        api.get(`/ingredients`), // FETCH ALL INGREDIENTS
      ]);

      setPantry(pantryRes.data);
      setRecipes(recipeRes.data);
      setRecipeIngredients(recipeIngRes.data);
      setShoppingList(shoppingRes.data);
      setAllIngredients(allIngRes.data); // SET ALL INGREDIENTS
      setMessage(""); 
    } catch (err) {
      console.error("Failed to fetch:", err);
      setMessage("Failed to fetch all data.");
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
      setMessage("Recipe added successfully! Now add ingredients below.");
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
      setMessage("Ingredient added to recipe successfully!");
      setNewRecipeIng({
        recipe_id: newRecipeIng.recipe_id, // Keep the recipe selected
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

  const generateShoppingList = async (recipeId) => {
    try {
      const res = await api.post(`/generate-shopping-list/${userId}/${recipeId}`);
      setMessage(res.data.message);
      await fetchData();
    } catch (err) {
      console.error("Error generating shopping list:", err);
      setMessage("Failed to generate shopping list. Check server logs for details.");
    }
  };

  const handleBuyShoppingItem = async (itemId) => {
    try {
      const res = await api.post(`/buy-item/${userId}/${itemId}`);
      setMessage(res.data.message);
      await fetchData();
    } catch (err) {
      console.error("Error buying item:", err);
      setMessage(`Failed to buy item: ${err.response?.data?.error || err.message}`);
    }
  };

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
      await fetchData();
    } catch (err) {
      console.error("Error buying new item:", err);
      setMessage(`Failed to buy item: ${err.response?.data?.error || err.message}`);
    }
  };

  // The logic for uniquePantryIngredients is now irrelevant for the recipe form 
  // but kept here just in case:
  // const uniquePantryIngredients = Array.from(new Set(pantry.map(p => p.ingredient_id)))
  //   .map(id => pantry.find(p => p.ingredient_id === id))
  //   .filter(p => p); 

  return (
    <div className="hc-wrapper">
      <div className="home-container">
        <h1>🍳 My Kitchen Management</h1>
        {message && <p className="message-box">{message}</p>}

        {/* Pantry Table */}
        <h2>🧺 My Pantry</h2>
        <table>
          <thead>
            <tr>
              <th>Ingredient</th>
              <th>Quantity</th>
              <th>Unit</th>
              <th>Expires</th>
            </tr>
          </thead>
          <tbody>
            {pantry.map((item) => (
              <tr key={item.id}>
                <td>{item.name}</td>
                <td>{item.quantity}</td>
                <td>{item.unit}</td>
                <td>{item.expiration_date}</td>
              </tr>
            ))}
          </tbody>
        </table>

        {/* Buy New Ingredient Form */}
        <div className="add-recipe-section">
          <h2>💸 Buy & Add New Ingredient to Pantry</h2>
          <form onSubmit={handleBuyNewPantryItem}>
            <div className="ingredient-row">
              <input
                type="text"
                placeholder="Ingredient Name (e.g., Flour, Milk)"
                value={newPantryItem.name}
                onChange={(e) => setNewPantryItem({ ...newPantryItem, name: e.target.value })}
                required
              />
              <input
                type="number"
                placeholder="Quantity"
                value={newPantryItem.quantity}
                onChange={(e) => setNewPantryItem({ ...newPantryItem, quantity: e.target.value })}
                required
              />
              <input
                type="text"
                placeholder="Unit (e.g., kg, L, pcs)"
                value={newPantryItem.unit}
                onChange={(e) => setNewPantryItem({ ...newPantryItem, unit: e.target.value })}
                required
              />
              <input
                type="date"
                title="Expiration Date (optional, defaults to 30 days)"
                value={newPantryItem.expiration_date}
                onChange={(e) => setNewPantryItem({ ...newPantryItem, expiration_date: e.target.value })}
              />
              <button type="submit" className="buy-new-btn">
                Add to Pantry
              </button>
            </div>
          </form>
        </div>
        
        {/* Shopping List */}
        <h2>🛒 Shopping List</h2>
        <table>
          <thead>
            <tr>
              <th>Ingredient</th>
              <th>Quantity</th>
              <th>Unit</th>
              <th>Action</th> 
            </tr>
          </thead>
          <tbody>
            {shoppingList.map((item) => (
              <tr key={item.id}>
                <td>{item.ingredient_name}</td>
                <td>{item.quantity}</td>
                <td>{item.unit}</td>
                <td>
                  <button
                    className="buy-btn"
                    onClick={() => handleBuyShoppingItem(item.id)}
                  >
                    Buy ✅
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>

        {/* Add Recipe Section */}
        <div className="add-recipe-section">
          <h2>🍲 Add New Recipe</h2>
          <form onSubmit={handleAddRecipe}>
            <input
              type="text"
              placeholder="Recipe Name"
              value={newRecipe.title}
              onChange={(e) =>
                setNewRecipe({ ...newRecipe, title: e.target.value })
              }
              required
            />
            <input
              type="text"
              placeholder="Short Description"
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

        {/* Add Ingredient to Recipe Section (Updated to use allKnownIngredients) */}
        <div className="add-recipe-section">
          <h2>➕ Add Ingredient to Recipe</h2>
          <form onSubmit={handleAddRecipeIngredient}>
            <div className="ingredient-row">
              {/* Select Recipe */}
              <select
                value={newRecipeIng.recipe_id}
                onChange={(e) =>
                  setNewRecipeIng({
                    ...newRecipeIng,
                    recipe_id: e.target.value,
                  })
                }
                required
              >
                <option value="">Select Recipe</option>
                {recipes.map((r) => (
                  <option key={r.id} value={r.id}>
                    {r.title}
                  </option>
                ))}
              </select>

              {/* Select Ingredient (from ALL known ingredients in DB) */}
              <select
                value={newRecipeIng.ingredient_id}
                onChange={(e) =>
                  setNewRecipeIng({
                    ...newRecipeIng,
                    ingredient_id: e.target.value,
                  })
                }
                required
              >
                <option value="">Select Ingredient (All Known)</option>
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
                  setNewRecipeIng({
                    ...newRecipeIng,
                    quantity: e.target.value,
                  })
                }
                required
              />
              {/* Unit */}
              <input
                type="text"
                placeholder="Unit (e.g. g, ml)"
                value={newRecipeIng.unit}
                onChange={(e) =>
                  setNewRecipeIng({
                    ...newRecipeIng,
                    unit: e.target.value,
                  })
                }
                required
              />
              <button type="submit" className="add-recipe-btn">
                Add Ingredient
              </button>
            </div>
          </form>
        </div>


        {/* Recipes List */}
        <h2>📖 My Recipes</h2>
        <ul>
          {recipes.map((r) => (
            <li key={r.id}>
              <strong>{r.title}</strong> — {r.description}
              <button
                className="generate-btn"
                onClick={() => generateShoppingList(r.id)}
              >
                Generate Shopping List 🛒
              </button>
            </li>
          ))}
        </ul>

        {/* Recipe Ingredients Table */}
        <h2>🧂 Recipe Ingredients Detail</h2>
        <table>
          <thead>
            <tr>
              <th>Recipe</th>
              <th>Ingredient</th>
              <th>Quantity</th>
              <th>Unit</th>
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
      </div>
    </div>
  );
};

export default Home;