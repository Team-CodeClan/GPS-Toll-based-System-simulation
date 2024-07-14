let journeyData = [];
let distances = [];
let fees = [];
document.addEventListener('DOMContentLoaded', function() {
    // Dummy admin credentials for login
    const adminCredentials = {
        username: 'admin',
        password: 'Admin@gps24'
    };
    
    // Elements
    const homeTab = document.getElementById('homeTab');
    const loginTab = document.getElementById('loginTab');
    const adminLogin = document.getElementById('adminLogin');
    const adminInterface = document.getElementById('adminInterface');
    const adminSearchForm = document.getElementById('adminSearchForm');
    const searchVehicleId = document.getElementById('searchVehicleId');
    const journeyDetails = document.getElementById('journeyDetails');
    const homeContent = document.getElementById('homeContent');
    
    const adminLoginForm = document.getElementById('adminLoginForm');
    const adminUsername = document.getElementById('adminUsername');
    const adminPassword = document.getElementById('adminPassword');
    const userTableBody = document.querySelector('#userTable tbody');
    const homeUserTableBody = document.createElement('tbody');
    
    // Admin login functionality
    adminLoginForm.addEventListener('submit', function(event) {
        event.preventDefault();
        const username = adminUsername.value;
        const password = adminPassword.value;
    
        if (username === adminCredentials.username && password === adminCredentials.password) {
            adminLogin.style.display = 'none';
            adminInterface.style.display = 'none';
            homeContent.style.display = 'block'; // Show home tab contents
            homeTab.click(); // Activate home tab
        } else {
            alert('Invalid credentials');
        }
    });
    function fetchAndDisplayUserData() {
        fetch('login.csv')
            .then(response => response.text())
            .then(data => {
                const rows = data.split('\n').slice(1);
                rows.forEach(row => {
                    const [username, password, userId, vehicleId] = row.split(',');
                    const tr = document.createElement('tr');
                    const tdUserId = document.createElement('td');
                    const tdVehicleId = document.createElement('td');
                    tdUserId.textContent = userId;
                    tdVehicleId.textContent = vehicleId;
                    tr.appendChild(tdUserId);
                    tr.appendChild(tdVehicleId);
                    userTableBody.appendChild(tr);
                });
            });
    }
    // Function to fetch journey data
    function fetchJourneyData(vehicleId) {
        const apiUrl = 'http://127.0.0.1:5001/predict'; // Replace with your Flask API URL
    
        // Prepare the request body
        const requestBody = {
            vehicle_id: vehicleId
        };
    
        // Send POST request to Flask API
        fetch(apiUrl, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(requestBody)
        })
        .then(response => {
            if (!response.ok) {
                throw new Error('Network response was not ok');
            }
            return response.json(); // Expecting JSON response
        })
        .then(data => {
            //console.log('Journey data fetched successfully:', data);
            let jsonObject = JSON.parse(data);
            // Loop through the JSON object and extract values
            jsonObject.forEach(item => {
                distances.push(item.distance);
                fees.push(item.fee);
            });
            displayJourneyData();
            // Now you have two arrays: distances and fees
           // console.log("Distances:", distances);
           // console.log("Fees:", fees);
        })
        .catch(error => {
            console.error('Error making POST request to Flask API:', error);
        });
    }

    // Handle search form submission
    adminSearchForm.addEventListener('submit', function(event) {
        event.preventDefault();
        const vehicleId = searchVehicleId.value;
        fetchJourneyData(vehicleId); // Fetch journey data for the entered vehicle ID
    });

    // Function to display journey data
    function displayJourneyData() {
        // Check if fees and distances are arrays and not empty
        if (Array.isArray(fees) && fees.length > 0 && Array.isArray(distances) && distances.length > 0) {
            // Update the table rows with journey details
            distances.forEach((distance, index) => {
                const fee = fees[index];
                const journeyNumber = index + 1;
    
                // Update table cells with journey data
                const distanceCell = document.getElementById(`j${journeyNumber}-distance`);
                const feeCell = document.getElementById(`j${journeyNumber}-fees`);
    
                if (distanceCell && feeCell) {
                    distanceCell.textContent = `${distance.toFixed(2)} m`;
                    feeCell.textContent = `Rs${fee.toFixed(2)}`;
                }
            });
    
            // Log the distances and fees for debugging
           // console.log("Distances:", distances);
          //  console.log("Fees:", fees);
    
            // Update the total distance and total toll
            const totalDistance = distances.reduce((acc, curr) => acc + parseFloat(curr), 0).toFixed(2);
            const totalToll = fees.reduce((acc, curr) => acc + parseFloat(curr), 0).toFixed(2);
    
            document.getElementById('totalDistance').textContent = `${totalDistance} m`;
            document.getElementById('totalToll').textContent = `Rs${totalToll}`;
    
        } else {
            console.error('Fees or distances array is not valid or is empty.');
        }
    }  

    // Tab navigation functionality
    homeTab.addEventListener('click', function() {
        adminLogin.style.display = 'none';
        adminInterface.style.display = 'block';
        journeyDetails.style.display = 'block';
        homeContent.style.display = 'block';
        fetchAndDisplayUserData();
    });
    
    loginTab.addEventListener('click', function() {
        adminLogin.style.display = 'block';
        adminInterface.style.display = 'none';
        journeyDetails.style.display = 'none';
        homeContent.style.display = 'none';
    });
    
    // Initial tab activation
    loginTab.click(); // Show login tab by default
});
