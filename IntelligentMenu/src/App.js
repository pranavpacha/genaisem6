const { useState, useEffect } = React;

const App = () => {
  const [searchResults, setSearchResults] = useState([]);
  const [isSearching, setIsSearching] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [allMenuItems, setAllMenuItems] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);

  // Load all menu items on component mount
  useEffect(() => {
    loadAllMenuItems();
  }, []);

  const loadAllMenuItems = async () => {
    try {
      setIsLoading(true);
      const response = await axios.get('/api/menu');
      setAllMenuItems(response.data.items);
      setSearchResults(response.data.items); // Show all items initially
      setError(null);
    } catch (error) {
      console.error('Error loading menu:', error);
      setError('Failed to load menu. Please make sure the backend is running on port 8000.');
    } finally {
      setIsLoading(false);
    }
  };

  const handleSearch = (query, results = null) => {
    setSearchQuery(query);
    setIsSearching(!!query);
    
    if (!query) {
      // Show all items when search is cleared
      setSearchResults(allMenuItems);
    } else if (results) {
      // Use provided search results
      setSearchResults(results);
    }
  };

  const handleSuggestionSelect = (suggestion) => {
    console.log('Selected suggestion:', suggestion);
  };

  const getResultsText = () => {
    if (isLoading) return 'Loading menu...';
    if (error) return 'Error loading menu';
    if (!searchQuery) return `Showing all ${allMenuItems.length} menu items`;
    if (searchResults.length === 0) return `No results found for "${searchQuery}"`;
    if (searchResults.length === 1) return `1 result found for "${searchQuery}"`;
    return `${searchResults.length} results found for "${searchQuery}"`;
  };

  if (isLoading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-purple-50">
        <div className="container mx-auto px-4 py-8">
          <div className="text-center">
            <div className="animate-spin rounded-full h-16 w-16 border-b-4 border-primary-500 mx-auto mb-4"></div>
            <h2 className="text-2xl font-bold text-gray-700">Loading Menu...</h2>
            <p className="text-gray-500 mt-2">Setting up AI-powered search...</p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-purple-50">
      {/* Header */}
      <header className="bg-white shadow-sm border-b border-gray-100">
        <div className="container mx-auto px-4 py-6">
          <div className="text-center mb-8">
            <h1 className="text-4xl font-bold text-gray-900 mb-2 flex items-center justify-center">
              <span className="mr-3">🍽️</span>
              Smart Menu Search
              <span className="ml-3">🔍</span>
            </h1>
            <p className="text-gray-600 text-lg">
              Discover authentic Indian dishes with intelligent, typo-tolerant search
            </p>
          </div>
          
          {/* Search Bar */}
          <SearchBar onSearch={handleSearch} onSuggestionSelect={handleSuggestionSelect} />
        </div>
      </header>

      {/* Main Content */}
      <main className="container mx-auto px-4 py-8">
        {/* Error Message */}
        {error && (
          <div className="mb-8 bg-red-50 border border-red-200 rounded-lg p-4">
            <div className="flex items-center">
              <i className="fas fa-exclamation-triangle text-red-500 mr-3"></i>
              <div>
                <h3 className="text-red-800 font-semibold">Connection Error</h3>
                <p className="text-red-700 text-sm mt-1">{error}</p>
                <button 
                  onClick={loadAllMenuItems}
                  className="mt-2 bg-red-100 hover:bg-red-200 text-red-800 px-3 py-1 rounded text-sm font-medium transition-colors"
                >
                  Retry
                </button>
              </div>
            </div>
          </div>
        )}

        {/* Results Header */}
        <div className="mb-6 flex items-center justify-between">
          <h2 className="text-2xl font-bold text-gray-900">
            {getResultsText()}
          </h2>
          
          {searchQuery && (
            <button
              onClick={() => handleSearch('')}
              className="flex items-center text-primary-600 hover:text-primary-700 font-medium transition-colors"
            >
              <i className="fas fa-times mr-2"></i>
              Clear Search
            </button>
          )}
        </div>

        {/* Search Results */}
        {searchResults.length > 0 ? (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {searchResults.map((item) => (
              <MenuCard key={item.id} item={item} />
            ))}
          </div>
        ) : !isLoading && !error && (
          <div className="text-center py-16">
            <div className="text-6xl mb-4">🔍</div>
            <h3 className="text-2xl font-bold text-gray-700 mb-2">No Results Found</h3>
            <p className="text-gray-500 mb-6">
              Try adjusting your search terms or check for typos.<br/>
              Our AI search is very forgiving with spelling mistakes!
            </p>
            <div className="space-y-2 text-sm text-gray-400">
              <p>💡 Try searching for:</p>
              <div className="flex flex-wrap justify-center gap-2 mt-2">
                {['dosa', 'biryani', 'chicken', 'paneer', 'curry', 'tandoori'].map(term => (
                  <button
                    key={term}
                    onClick={() => handleSearch(term)}
                    className="bg-gray-100 hover:bg-primary-100 text-gray-600 hover:text-primary-700 px-3 py-1 rounded-full text-sm transition-colors"
                  >
                    {term}
                  </button>
                ))}
              </div>
            </div>
          </div>
        )}
      </main>

      {/* Footer */}
      <footer className="bg-gray-50 border-t border-gray-100 mt-16">
        <div className="container mx-auto px-4 py-8 text-center">
          <p className="text-gray-600 mb-2">
            🚀 Powered by PostgreSQL database and intelligent search
          </p>
          <p className="text-sm text-gray-500">
            Try searching with typos like "dsoa" for "dosa" or "chiken" for "chicken" - all prices in Indian Rupees
          </p>
        </div>
      </footer>
    </div>
  );
};

// Export for use in index.js
window.App = App;
