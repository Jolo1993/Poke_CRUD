document.addEventListener('DOMContentLoaded', function() {
    const searchInput = document.getElementById('search-input');
    const searchButton = document.getElementById('search-button');
    const resultsContainer = document.getElementById('results-container');
    const indexCheckboxes = document.getElementById('index-checkbox');
    loadIndexes();

    // Search functionality
    searchButton.addEventListener('click', performSearch);
    searchInput.addEventListener('keypress', function(e) {
        if (e.key === 'Enter') {
            performSearch();
        }
    });

    // Function to perform search
function performSearch() {
    const searchInput = document.getElementById('search-input');
    const query = searchInput.value.trim();

    if (!query) {
        displayResults([]);
        return;
    }

    // Get selected indexes
    const selectedIndexes = [];
    document.querySelectorAll('input[name="index"]:checked').forEach(checkbox => {
        selectedIndexes.push(checkbox.value);
    });

    if (selectedIndexes.length === 0) {
        selectedIndexes.push('pokemon'); // Default to Pokemon index
    }

    // Create JSON payload for POST request
    const searchPayload = {
        query: query,
        indexes: selectedIndexes,
        max_hits: 20
    };

    const resultsContainer = document.getElementById('results-container');
    resultsContainer.innerHTML = '<p>Searching...</p>';

    // Send POST request with JSON payload
    fetch('/search', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(searchPayload)
    })
    .then(response => response.json())
    .then(data => {
        console.log("Search results:", data);

        if (data.error) {
            resultsContainer.innerHTML = `<p>Error: ${data.error}</p>`;
            return;
        }

        displayResults(data.results || []);

        // Update counts
        const totalElement = document.getElementById('result-count');
        if (totalElement) {
            totalElement.textContent = `Found ${data.total || 0} results`;
        }
    })
    .catch(error => {
        console.error("Search error:", error);
        resultsContainer.innerHTML = `<p>Error: ${error.message}</p>`;
    });
}

    // Function to display results
    function displayResults(results) {
        resultsContainer.innerHTML = '';

        results.forEach(result => {
            const pokemon = result.document;
            const card = document.createElement('div');
            card.className = 'pokemon-card';

            // Create HTML for the Pokemon card
            card.innerHTML = `
                <div class="pokemon-image">
                    <img src="${pokemon.sprites?.front_default || ''}" alt="${pokemon.name}">
                </div>
                <div class="pokemon-info">
                    <h3>${pokemon.name} (#${pokemon.id})</h3>
                    <p>Types: ${pokemon.types.map(t => t.type.name).join(', ')}</p>
                    <p>Height: ${pokemon.height/10}m, Weight: ${pokemon.weight/10}kg</p>
                    <p>Base Experience: ${pokemon.base_experience}</p>
                </div>
            `;

            resultsContainer.appendChild(card);
        });
    }

    function loadIndexes() {
        console.log("Loading indexes...");  // Debug log

        fetch('/indexes')
            .then(response => {
                console.log("Got response:", response.status);  // Debug log
                return response.json();
            })
            .then(indexes => {
                console.log("Parsed data:", indexes);  // Debug log

                const indexCheckboxes = document.getElementById('index-checkboxes');
                if (!indexCheckboxes) {
                    console.error("Could not find index-checkboxes element!");
                    return;
                }

                indexCheckboxes.innerHTML = '';

                if (!indexes || indexes.length === 0) {
                    indexCheckboxes.innerHTML = '<p>No indexes available</p>';
                    return;
                }

                // Create checkbox for each index
                indexes.forEach(index => {
                    const checkbox = document.createElement('div');
                    checkbox.className = 'index-checkbox';
                    checkbox.innerHTML = `
                        <label>
                            <input type="checkbox" name="index" value="${index.id}" 
                                ${index.id === 'pokemon' ? 'checked' : ''}>
                            ${index.id}
                        </label>
                    `;
                    indexCheckboxes.appendChild(checkbox);
                });
            })
            .catch(error => {
                console.error("Error loading indexes:", error);  // Debug log
                const indexCheckboxes = document.getElementById('index-checkboxes');
                if (indexCheckboxes) {
                    indexCheckboxes.innerHTML = `<p>Error loading indexes: ${error.message}</p>`;
                }
            });
}
});

