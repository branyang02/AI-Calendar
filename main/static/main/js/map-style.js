// global var to store all markers
var allMarkers = [];
var map;


function initMap(filter, favorite_locations) {
    var myMapID = "142f8a11c8136ffb"
    var placePins = false
    if(filter==="food") {
        myMapID = "dfc975942ffdcbbf"
    }
    else if(filter==="rec") {
        myMapID = "fcf6fc4a3eab8634"
    }
    else if(filter==="study") {
        myMapID = "16b66fa23e722722"
    }
    else if(filter==="favorites") {
        myMapID = "9cea4dea7b784c37"
        placePins = true
    }

    var minLat = 38.038000
    var maxLat = 38.0328636
    
    var minLng = -78.549722
    var maxLng = -78.437274

    var cvilleArea = new google.maps.LatLngBounds(
        new google.maps.LatLng(minLat, minLng), 
        new google.maps.LatLng(maxLat, maxLng)
    );

    map = new google.maps.Map(document.getElementById("map"), {
        center: { lat: 38.033554, lng: -78.50798 },
        zoom: 15,
        mapId: myMapID,
       
    });

    map.fitBounds(cvilleArea);

    if(placePins) {
        for(let i=0; i < favorite_locations.length; i++) {
            placePinOnMap(favorite_locations[i].fields.address, favorite_locations[i].fields.name)
        }
    }
}



function placePinOnMap(address, name) {
    const geocoder = new google.maps.Geocoder();
    geocoder.geocode({ address: address }, function (results, status) {
        if (status === "OK") {
            const location = results[0].geometry.location;
            
            //gets latitude and longitude from location
            var markerLat = location.lat();
            var markerLng = location.lng(); 

            //checks if address is in the Charlottesville area
            if(markerLat > 38.00 && markerLat < 38.05 && markerLng > -78.53 && markerLng < -78.42){

                const marker = new google.maps.Marker({
                    map: map,
                    position: location,
                    title: address, // display address when marker is hovered
                });


                allMarkers.push(marker);
            
                // Create an InfoWindow
                const infoWindow = new google.maps.InfoWindow({
                    content: `<div style='color: black;'>${name}</div>`,
                });

                infoWindow.open(map, marker);

                // Add a click listener to the marker to open the InfoWindow
                marker.addListener("click", function () {
                    infoWindow.open(map, marker);
                });
            }


            // map.setCenter(location);
        } else {
            console.error(
                "Geocode was not successful for the following reason:",
                status
            );
        }
    });
}

function clearAllMarkers() {
    console.log("Clearing all markers, count:", allMarkers.length);

    for (let i = 0; i < allMarkers.length; i++) {
        allMarkers[i].setMap(null);
    }
    allMarkers = [];
}

document.addEventListener("DOMContentLoaded", function () {
    const inputElement = document.getElementById("exampleFormControlInput1");
    const dynamicContent = document.getElementById("dynamicContent");
    const inputContainer = document.querySelector(".input-container");

    const formElement = document.querySelector("form"); // or use the specific selector if you have multiple forms

    if (formElement) {
        formElement.addEventListener("submit", function (e) {
            e.preventDefault();
        });
    }

    function sendMessage() {
        const message = inputElement.value;
        if (message.trim() !== "") {
            const sendIcon = inputContainer.querySelector(".send-icon");
            const spinner = inputContainer.querySelector(".spinner-loading");

            // Hide send icon and show spinner
            sendIcon.style.display = "none";
            spinner.style.display = "inline-block";

            console.log(message);
            addUserMessage(message);

            fetch("/map/chat/", {
                method: "POST",
                headers: {
                    "X-Requested-With": "XMLHttpRequest",
                    "Content-Type": "application/x-www-form-urlencoded",
                    "X-CSRFToken": getCookie("csrftoken"),
                },
                body: `message=${encodeURIComponent(message)}`,
            })
                .then((response) => response.json())
                .then((data) => {
                    // Clear All previous markers
                    clearAllMarkers();
                    // If there are addresses, display them on the map
                    if (
                        data.addresses.addresses &&
                        data.addresses.addresses.length > 0
                    ) {
                        for (
                            let i = 0;
                            i < data.addresses.addresses.length && i < 5;
                            i++
                        ) {
                            placePinOnMap(
                                data.addresses.addresses[i],
                                data.addresses.location_names[i]
                            );
                        }
                    }
                    return addAssistantMessage(data.response);
                })
                .then(() => {
                    // Hide spinner and show send icon AFTER message is fully displayed
                    sendIcon.style.display = "inline-block";
                    spinner.style.display = "none";
                })
                .catch((error) => {
                    sendIcon.style.display = "inline-block";
                    spinner.style.display = "none";
                    console.error("There was an error!", error);
                });

            inputElement.value = ""; // Clear the input field
        }
    }

    inputElement.addEventListener("keyup", function (e) {
        if (e.key === "Enter" || e.keyCode === 13) {
            e.preventDefault();
            e.stopPropagation();
            sendMessage();
        }
    });

    inputContainer.addEventListener("click", function (e) {
        if (
            e.target.closest(".send-icon") ||
            e.target.closest(".spinner-loading")
        ) {
            sendMessage();
        }
    });

    function addUserMessage(message) {
        let userMsgDiv = document.createElement("div");
        userMsgDiv.classList.add("user-message");
        userMsgDiv.textContent = `${message}`;
        dynamicContent.appendChild(userMsgDiv);
        dynamicContent.style.visibility = "visible"; // Make the dynamicContent visible when messages are added
        dynamicContent.scrollTop = dynamicContent.scrollHeight; // Auto-scroll to the latest message
    }

    function addAssistantMessage(message) {
        return new Promise((resolve) => {
            let assistantMsgDiv = document.createElement("div");
            assistantMsgDiv.classList.add("assistant-message");
            dynamicContent.appendChild(assistantMsgDiv);
            dynamicContent.scrollTop = dynamicContent.scrollHeight;

            let lines = message.split("\n");
            let currentLine = 0;
            let currentWordIndex = 0;
            let currentSpan;

            function createNewLine() {
                if (currentSpan) {
                    // Add a line break if it's not the first span
                    assistantMsgDiv.appendChild(document.createElement("br"));
                }
                currentSpan = document.createElement("span");
                assistantMsgDiv.appendChild(currentSpan);
            }

            function displayNextWord() {
                if (currentLine < lines.length) {
                    let words = lines[currentLine].split(" ");

                    if (currentWordIndex === 0) {
                        createNewLine();
                    }

                    if (currentWordIndex < words.length) {
                        currentSpan.textContent +=
                            (currentWordIndex === 0 ? "" : " ") +
                            words[currentWordIndex];
                        currentWordIndex++;
                        dynamicContent.scrollTop = dynamicContent.scrollHeight;
                        setTimeout(displayNextWord, 50);
                    } else {
                        currentLine++;
                        currentWordIndex = 0;
                        setTimeout(displayNextWord, 50);
                    }
                } else {
                    resolve();
                }
            }

            displayNextWord();
        });
    }

    function getCookie(name) {
        let cookieValue = null;
        if (document.cookie && document.cookie !== "") {
            const cookies = document.cookie.split(";");
            for (let i = 0; i < cookies.length; i++) {
                const cookie = cookies[i].trim();
                if (cookie.substring(0, name.length + 1) === name + "=") {
                    cookieValue = decodeURIComponent(
                        cookie.substring(name.length + 1)
                    );
                    break;
                }
            }
        }
        return cookieValue;
    }
});
