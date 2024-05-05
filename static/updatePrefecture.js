const updatePrefecture = () => {
    const selectedPrefecture = document.getElementById("prefecture").value;
    const responseMessage = document.getElementById("responseMessage");
    console.log(selectedPrefecture)

    fetch(`/update_prefecture/${selectedPrefecture}`)
        .then(response => response.json())
        .then(data => {
            responseMessage.textContent = data.message;
        })
        .catch(error => {
            responseMessage.textContent = "An error occurred.";
        });
};
