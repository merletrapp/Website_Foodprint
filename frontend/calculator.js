document.addEventListener("DOMContentLoaded", () => {
    const foodInput = document.getElementById("food-name");
    const amountInput = document.getElementById("amount");
    const unitSelect = document.getElementById("unit");

    const addButton = document.querySelector(".btn-calculator-add");
    const calcButton = document.querySelector(".btn-calculator-calc");

    const summaryCount = document.querySelector(".summary-count");
    const summaryList = document.querySelector(".summary-list");
    const resultValue = document.querySelector(".result-value");

    // API-Payload: [{ food_id, amount, unit }]
    const apiItems = [];

    // UI-Liste: [{ food_id, name, amount, unit }]
    const uiItems = [];

    addButton.addEventListener("click", handleAddFood);
    calcButton.addEventListener("click", handleCalculate);

    // ENTER im Mengenfeld = hinzufügen
    amountInput.addEventListener("keydown", (e) => {
        if (e.key === "Enter") {
            e.preventDefault();
            handleAddFood();
        }
    });

    async function handleAddFood() {
        const name = foodInput.value.trim();
        const amount = parseFloat(amountInput.value);
        const unit = unitSelect.value; // g, kg, ml, l

        if (!name) {
            alert("Bitte ein Lebensmittel eingeben.");
            return;
        }
        if (isNaN(amount) || amount <= 0) {
            alert("Bitte eine gültige Menge größer 0 eingeben.");
            return;
        }

        try {
            const foodData = await fetchFoodByName(name); // -> erstes Suchergebnis (Objekt) oder null

            if (!foodData || !foodData.id) {
                alert("Lebensmittel nicht gefunden.");
                return;
            }

            apiItems.push({
                food_id: foodData.id,
                amount: amount,
                unit: unit
            });

            uiItems.push({
                food_id: foodData.id,
                name: foodData.name || name,
                amount: amount,
                unit: unit
            });

            updateMealSummary();
            clearFormInputs();
            console.log("Payload für /api/calc/meal/:", { items: apiItems });
        } catch (err) {
            console.error(err);
            alert("Fehler bei der Lebensmittelsuche. Bitte API/Server prüfen.");
        }
    }

    async function handleCalculate() {
        if (apiItems.length === 0) {
            alert("Bitte zuerst mindestens ein Lebensmittel hinzufügen.");
            return;
        }

        try {
            const response = await fetch("http://127.0.0.1:8000/api/foods/calculate/", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ items: apiItems })
            });

            const text = await response.text();

            if (!response.ok) {
                console.error("API-Fehler:", response.status, text);
                alert(`Fehler bei der Berechnung (${response.status}). Details: ${text}`);
                return;
            }

            const data = JSON.parse(text);
            const total = typeof data.total_co2 === "number" ? data.total_co2 : 0;
            resultValue.textContent = `${total.toFixed(2)} kg CO₂e`;
        } catch (err) {
            console.error(err);
            alert("Netzwerkfehler bei der Berechnung.");
        }
    }

    function updateMealSummary() {
        summaryCount.textContent = `${uiItems.length} Einträge`;
        summaryList.innerHTML = "";

        if (uiItems.length === 0) {
            const li = document.createElement("li");
            li.classList.add("summary-placeholder");
            li.textContent = "Noch keine Lebensmittel hinzugefügt";
            summaryList.appendChild(li);
            return;
        }

        uiItems.forEach((item) => {
            const li = document.createElement("li");
            li.classList.add("summary-item");
            li.textContent = `${item.name} – ${item.amount} ${item.unit}`;
            summaryList.appendChild(li);
        });
    }

    function clearFormInputs() {
        foodInput.value = "";
        amountInput.value = "";
        unitSelect.value = "g";
        foodInput.focus();
    }

    // Sucht über /api/foods/?q=<name> (liefert LISTE)
    async function fetchFoodByName(name) {
        const url = `http://127.0.0.1:8000/api/foods/?q=${encodeURIComponent(name)}`;
        const res = await fetch(url);

        if (!res.ok) {
            const errText = await res.text();
            throw new Error(`Search failed (${res.status}): ${errText}`);
        }

        const data = await res.json(); // erwartet Array
        return Array.isArray(data) && data.length > 0 ? data[0] : null;
    }
});