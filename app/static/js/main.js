/**
 * Pokémon Quickwit Visualizer
 * Main application functionality
 */
document.addEventListener('DOMContentLoaded', function() {
    // DOM elements
    const searchInput = document.getElementById('search-input');
    const searchButton = document.getElementById('search-button');
    const resultsContainer = document.getElementById('results-container');

    // Initialize
    loadIndexes();

    // Event listeners
    searchButton.addEventListener('click', performSearch);
    searchInput.addEventListener('keypress', function(e) {
        if (e.key === 'Enter') {
            performSearch();
        }
    });

    /**
     * Load and display available indexes from the API
     */
    function loadIndexes() {
        const indexCheckboxes = document.getElementById('index-checkboxes');

        if (!indexCheckboxes) {
            console.error("Element 'index-checkboxes' not found");
            return;
        }

        indexCheckboxes.innerHTML = '<div class="loading">Loading indexes...</div>';

        fetch('/indexes')
            .then(response => {
                if (!response.ok) {
                    throw new Error(`Server returned ${response.status}: ${response.statusText}`);
                }
                return response.json();
            })
            .then(indexes => {
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
                console.error("Error loading indexes:", error);
                indexCheckboxes.innerHTML = `<p>Error loading indexes: ${error.message}</p>`;
            });
    }

    /**
     * Perform search based on input and selected indexes
     */
    function performSearch() {
        const searchInput = document.getElementById('search-input');
        const query = searchInput.value.trim();
    
        if (!query) {
            displayResults([]);
            updateResultCount(0);
            return;
        }
    
        // Get selected indexes from checkboxes
        const selectedIndexes = Array.from(
            document.querySelectorAll('input[name="index"]:checked')
        ).map(checkbox => checkbox.value);
    
        // Use default if nothing selected
        if (selectedIndexes.length === 0) {
            selectedIndexes.push('pokemon');
        }
    
        // Format the query for Quickwit
        let formattedQuery = query;
    
        // Check if it's a simple query or already formatted with field names
        if (!query.includes(':')) {
            // For simple queries, search in name and _all_text
            formattedQuery = `documents.name:${query} OR documents._all_text:${query}`;
    
            // Special handling for type searches
            if (['normal', 'fire', 'water', 'electric', 'grass', 'ice', 
                 'fighting', 'poison', 'ground', 'flying', 'psychic', 
                 'bug', 'rock', 'ghost', 'dragon', 'dark', 'steel', 'fairy'].includes(query.toLowerCase())) {
                formattedQuery = `types:${query}`;
            }
    
            // Special handling for legendary/mythical
            if (query.toLowerCase() === 'legendary') {
                formattedQuery = 'is_legendary:true';
            } else if (query.toLowerCase() === 'mythical') {
                formattedQuery = 'is_mythical:true';
            }
        }
    
        // Create JSON payload for POST request
        const searchPayload = {
            query: formattedQuery,
            indexes: selectedIndexes,
            max_hits: 20
        };
    
        console.log("Search query:", formattedQuery);
        resultsContainer.innerHTML = '<p class="loading">Searching...</p>';
    
        // Send POST request with JSON payload
        fetch('/search', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(searchPayload)
        })
        .then(response => {
            if (!response.ok) {
                throw new Error(`Server returned ${response.status}: ${response.statusText}`);
            }
            return response.json();
        })
        .then(data => {
            if (data.error) {
                throw new Error(data.error);
            }
    console.log("Full search response:", data);
    console.log("Results array:", data.results);
    if (data.debug_raw_response) {
        console.log("Raw API response:", data.debug_raw_response);
    }
            console.log("Search response:", data);
            displayResults(data.results || []);
            updateResultCount(data.total || 0);
        })
        .catch(error => {
            console.error("Search error:", error);
            resultsContainer.innerHTML = `<p class="error">Error: ${error.message}</p>`;
            updateResultCount(0);
        });
    }
    
    function updateResultCount(count) {
        const totalElement = document.getElementById('result-count');
        if (totalElement) {
            totalElement.textContent = `Found ${count} results`;
        } else {
            const countElement = document.createElement('div');
            countElement.id = 'result-count';
            countElement.textContent = `Found ${count} results`;
            document.querySelector('.search-section').appendChild(countElement);
        }
    }

    /**
     * Display search results in the UI
     */
    /**
     * Display search results in the UI
     */
    function displayResults(results) {
        resultsContainer.innerHTML = '';
    
        if (results.length === 0) {
            resultsContainer.innerHTML = `
                <div class="no-results">
                    <p>No Pokémon found. Try searching for:</p>
                    <ul class="search-suggestions">
                        <li><a href="#" onclick="document.getElementById('search-input').value='pikachu'; performSearch(); return false;">pikachu</a></li>
                        <li><a href="#" onclick="document.getElementById('search-input').value='steel'; performSearch(); return false;">steel</a></li>
                        <li><a href="#" onclick="document.getElementById('search-input').value='legendary'; performSearch(); return false;">legendary</a></li>
                    </ul>
                </div>
            `;
            return;
        }
    
        results.forEach(pokemon => {
            const card = document.createElement('div');
            card.className = 'pokemon-card';
    
            // Extract type names from the nested structure
            let typeNames = [];
            if (pokemon.types && Array.isArray(pokemon.types)) {
                // Sort by slot to ensure primary type comes first
                const sortedTypes = [...pokemon.types].sort((a, b) => a.slot - b.slot);
                typeNames = sortedTypes.map(typeObj => typeObj.type?.name || 'Unknown');
            }
    
            // Format type badges
            const typeBadges = typeNames.map(type => 
                `<span class="type-badge type-${type}">${type}</span>`
            ).join('');
    
            // Extract stats
            const stats = {};
            if (pokemon.stats && Array.isArray(pokemon.stats)) {
                pokemon.stats.forEach(statObj => {
                    const statName = statObj.stat?.name || 'unknown';
                    stats[statName] = statObj.base_stat;
                });
            }
    
            // Get the sprite URL - prefer official artwork if available
            let spriteUrl = '';
            if (pokemon.sprites) {
                if (pokemon.sprites.other && pokemon.sprites.other['official-artwork']) {
                    spriteUrl = pokemon.sprites.other['official-artwork'].front_default;
                } else if (pokemon.sprites.front_default) {
                    spriteUrl = pokemon.sprites.front_default;
                }
            }
    
            // Extract ability names
            const abilities = [];
            if (pokemon.abilities && Array.isArray(pokemon.abilities)) {
                pokemon.abilities.forEach(abilityObj => {
                    if (abilityObj.ability && abilityObj.ability.name) {
                        const abilityName = abilityObj.ability.name;
                        const isHidden = abilityObj.is_hidden;
                        abilities.push({
                            name: abilityName,
                            isHidden: isHidden
                        });
                    }
                });
            }
    
            // Format abilities text
            let abilitiesText = 'None';
            if (abilities.length > 0) {
                const regularAbilities = abilities.filter(a => !a.isHidden).map(a => a.name);
                const hiddenAbilities = abilities.filter(a => a.isHidden).map(a => a.name);
    
                abilitiesText = regularAbilities.join(', ');
                if (hiddenAbilities.length > 0) {
                    abilitiesText += ` (Hidden: ${hiddenAbilities.join(', ')})`;
                }
            }
    
            // Create HTML for the Pokemon card
            card.innerHTML = `
                <div class="pokemon-image">
                    ${spriteUrl ? 
                        `<img src="${spriteUrl}" alt="${pokemon.name || 'Unknown'}" 
                          onerror="this.onerror=null; this.src='data:image/svg+xml;utf8,<svg xmlns=\\'http://www.w3.org/2000/svg\\' width=\\'120\\' height=\\'120\\'><rect width=\\'120\\' height=\\'120\\' fill=\\'%23f0f0f0\\'/><text x=\\'50%\\' y=\\'50%\\' dominant-baseline=\\'middle\\' text-anchor=\\'middle\\' font-size=\\'48\\' fill=\\'%23999\\'>?</text></svg>';">` : 
                        `<div class="placeholder-image">?</div>`
                    }
                </div>
                <div class="pokemon-info">
                    <div class="pokemon-header">
                        <h3>${pokemon.name || 'Unknown'} 
                            ${pokemon.id ? `<span class="pokemon-id">#${pokemon.id}</span>` : ''}
                        </h3>
                        <div class="pokemon-types">${typeBadges}</div>
                    </div>
    
                    <div class="pokemon-details">
                        <p><strong>Species:</strong> ${pokemon.species?.name || 'Unknown'}</p>
                        <p><strong>Height:</strong> ${pokemon.height ? `${(pokemon.height/10).toFixed(1)}m` : 'Unknown'}</p>
                        <p><strong>Weight:</strong> ${pokemon.weight ? `${(pokemon.weight/10).toFixed(1)}kg` : 'Unknown'}</p>
                        <p><strong>Abilities:</strong> ${abilitiesText}</p>
                    </div>
    
                    <div class="pokemon-stats">
                        <h4>Base Stats</h4>
                        <table class="stats-table">
                            <tr>
                                <td>HP</td>
                                <td>Attack</td>
                                <td>Defense</td>
                            </tr>
                            <tr>
                                <td>${stats['hp'] || '?'}</td>
                                <td>${stats['attack'] || '?'}</td>
                                <td>${stats['defense'] || '?'}</td>
                            </tr>
                            <tr>
                                <td>Sp. Atk</td>
                                <td>Sp. Def</td>
                                <td>Speed</td>
                            </tr>
                            <tr>
                                <td>${stats['special-attack'] || '?'}</td>
                                <td>${stats['special-defense'] || '?'}</td>
                                <td>${stats['speed'] || '?'}</td>
                            </tr>
                        </table>
                    </div>
                </div>
            `;
    
            resultsContainer.appendChild(card);
        });
    }

    // Expose performSearch to global scope for the suggestion links
    window.performSearch = performSearch;
});
