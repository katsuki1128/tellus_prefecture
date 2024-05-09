// updateCities.js

const initializeFormSubmission = (formId) => {
    const imageForm = document.getElementById(formId);
    if (imageForm) {
        imageForm.onsubmit = (event) => {
            event.preventDefault();  // デフォルトのフォーム送信を防止
            const tellusName = document.getElementById("tellus_name").value;
            console.log("tellus:name:", tellusName);
            imageForm.submit();  // その後、手動でフォーム送信
        };
    }
};

const updatePrefecture = () => {
    const selectedPrefectureCode = document.getElementById("prefecture").value;
    console.log(selectedPrefectureCode)
    const cityDropdown = document.getElementById("city_name");

    if (!selectedPrefectureCode) {
        cityDropdown.innerHTML = "<option value=''>市区町村</option>";
        return;
    }

    fetch(`/update_prefecture/${selectedPrefectureCode}`)
        .then(response => response.json())
        .then(data => {
            console.log(data);
            // Clear the current city options
            cityDropdown.innerHTML = "<option value=''>市区町村</option>";

            // Populate the city dropdown with the received cities
            if (data.city_names) {
                for (const city of data.city_names) {
                    const option = document.createElement("option");
                    option.value = city;
                    option.text = city;
                    cityDropdown.appendChild(option);
                }
            } else {
                document.getElementById("responseMessage").textContent = "Error: " + data.error;
            }

            const selectedCity = cityDropdown.getAttribute("data-selected-city");
            if (selectedCity) {
                cityDropdown.value = selectedCity;
            }
        })
        .catch(error => {
            console.error("Error:", error);
        });
};

const updateCity = () => {
    const selectedCity = document.getElementById("city_name").value;
    const selectedPrefecture = document.getElementById("prefecture").value;

    fetch("/", {
        method: "POST",
        headers: {
            "Content-Type": "application/x-www-form-urlencoded",
        },
        body: new URLSearchParams({
            "prefecture": selectedPrefecture,
            "city_name": selectedCity,
            "action": "get_map",
        }),
    })
        .then(response => response.text())
        .then(html => {
            document.open();
            document.write(html);
            document.close();
        })
        .catch(error => {
            console.error("Error:", error);
        });
};

window.onload = () => {
    initializeFormSubmission("imageForm");
    updatePrefecture();
};
