import React from "react";
import "../styles/Home.css";
import { useEffect, useState } from "react";
import api from "../axiosConfig";

const Home = () => {
  const userId = "93f5fed8-c2cd-4e70-a7a4-19b3a9506b25";

  const [pantry, setPantry] = useState([]);
  const [recipes, setRecipes] = useState([]);
  const [recipeIngredients, setRecipeIngredients] = useState([]);
  const [shoppingList, setShoppingList] = useState([]);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const [pantryRes, recipeRes, recipeIngRes, shoppingRes] = await Promise.all([
          api.get(`/pantry/${userId}`),
          api.get(`/recipes/${userId}`),
          api.get(`/recipe-ingredients/${userId}`),
          api.get(`/shopping-list/${userId}`)
        ]);

        setPantry(pantryRes.data);
        setRecipes(recipeRes.data);
        setRecipeIngredients(recipeIngRes.data);
        setShoppingList(shoppingRes.data);
      } catch (err) {
        console.error("Failed to fetch:", err);
      }
    };
    fetchData();
  }, []);

  return (
    <div className="hc-wrapper">
      <div className="home-container">
        <h1>🍳 My Pantry</h1>
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

        <h2>📖 My Recipes</h2>
        <ul>
          {recipes.map((r) => (
            <li key={r.id}>
              <strong>{r.title}</strong> — {r.description}
            </li>
          ))}
        </ul>

        <h2>🧂 Recipe Ingredients</h2>
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

        <h2>🛒 Shopping List</h2>
        <table>
          <thead>
            <tr>
              <th>Ingredient</th>
              <th>Quantity</th>
              <th>Unit</th>
            </tr>
          </thead>
          <tbody>
            {shoppingList.map((item) => (
              <tr key={item.id}>
                <td>{item.ingredient_name}</td>
                <td>{item.quantity}</td>
                <td>{item.unit}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};

export default Home;