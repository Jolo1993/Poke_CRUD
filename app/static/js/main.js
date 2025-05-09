document.addEventListener('DOMContentLoaded', function() {
    const searchInput = document.getElementById('search-input');
    const searchButton = document.getElementById('search-button');
    const resultsContainer = document.getElementById('results-container');

    // Search functionality
    searchButton.addEventListener('click', performSearch);
    searchInput.addEventListener('keypress', function(e) {
        if (e.key === 'Enter') {
            performSearch();
        }
    });

    // Function to perform search
    function performSearch() {
        const query = searchInput.value.trim();

        if (!query) {
            resultsContainer.innerHTML = '<p>Please enter a search term</p>';
            return;
        }

        resultsContainer.innerHTML = '<p>Searching...</p>';

        fetch(`/search?query=${encodeURIComponent(query)}`)
            .then(response => response.json())
            .then(data => {
                if (data.error) {
                    resultsContainer.innerHTML = `<p>Error: ${data.error}</p>`;
                    return;
                }

                if (!data.results || data.results.length === 0) {
                    resultsContainer.innerHTML = '<p>No results found</p>';
                    return;
                }

                displayResults(data.results);
            })
            .catch(error => {
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
});

