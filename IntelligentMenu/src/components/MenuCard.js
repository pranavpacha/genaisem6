 const { useState } = React;

const MenuCard = ({ item }) => {
  const [imageError, setImageError] = useState(false);

  const getCategoryColor = (category) => {
    const colors = {
      'North Indian': 'bg-orange-100 text-orange-800',
      'South Indian': 'bg-green-100 text-green-800',
      'Biryani': 'bg-yellow-100 text-yellow-800',
      'Tandoori': 'bg-red-100 text-red-800',
      'Street Food': 'bg-purple-100 text-purple-800',
      'Desserts': 'bg-pink-100 text-pink-800',
    };
    return colors[category] || 'bg-gray-100 text-gray-800';
  };

  const getDietaryColor = (dietary) => {
    const colors = {
      'vegetarian': 'bg-green-100 text-green-700',
      'vegan': 'bg-green-200 text-green-800',
      'gluten-free': 'bg-blue-100 text-blue-700',
      'contains dairy': 'bg-yellow-100 text-yellow-700',
      'contains gluten': 'bg-orange-100 text-orange-700',
      'pescatarian': 'bg-cyan-100 text-cyan-700',
      'contains shellfish': 'bg-red-100 text-red-700',
      'contains nuts': 'bg-amber-100 text-amber-700',
      'contains pork': 'bg-rose-100 text-rose-700',
    };
    return colors[dietary] || 'bg-gray-100 text-gray-700';
  };

  const getCategoryIcon = (category) => {
    const icons = {
      'North Indian': '🍛',
      'South Indian': '🥞',
      'Biryani': '🍚',
      'Tandoori': '🔥',
      'Street Food': '🥟',
      'Desserts': '🍰',
    };
    return icons[category] || '🍽️';
  };

  return (
    <div className="bg-white rounded-xl shadow-lg hover:shadow-xl transition-all duration-300 overflow-hidden border border-gray-100 hover:border-primary-300">
      {/* Header with category and similarity score */}
      <div className="p-4 pb-2">
        <div className="flex justify-between items-start mb-2">
          <span className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium ${getCategoryColor(item.category)}`}>
            <span className="mr-1">{getCategoryIcon(item.category)}</span>
            {item.category}
          </span>
          {item.similarity_score && (
            <span className="text-xs text-gray-500 bg-gray-100 px-2 py-1 rounded-full">
              {Math.round(item.similarity_score * 100)}% match
            </span>
          )}
        </div>
        
        {/* Item name */}
        <h3 className="text-xl font-bold text-gray-900 mb-2 leading-tight">
          {item.name}
        </h3>
        
        {/* Description */}
        <p className="text-gray-600 text-sm leading-relaxed mb-3">
          {item.description}
        </p>
      </div>

      {/* Ingredients */}
      <div className="px-4 pb-2">
        <h4 className="text-sm font-semibold text-gray-700 mb-2 flex items-center">
          <i className="fas fa-list-ul mr-2 text-gray-500"></i>
          Ingredients
        </h4>
        <div className="flex flex-wrap gap-1">
          {item.ingredients && item.ingredients.map((ingredient, index) => (
            <span
              key={index}
              className="inline-block bg-gray-100 text-gray-700 text-xs px-2 py-1 rounded-full"
            >
              {ingredient}
            </span>
          ))}
        </div>
      </div>

      {/* Dietary information */}
      {item.dietary_info && item.dietary_info.length > 0 && (
        <div className="px-4 pb-3">
          <h4 className="text-sm font-semibold text-gray-700 mb-2 flex items-center">
            <i className="fas fa-info-circle mr-2 text-gray-500"></i>
            Dietary Info
          </h4>
          <div className="flex flex-wrap gap-1">
            {item.dietary_info.map((dietary, index) => (
              <span
                key={index}
                className={`inline-block text-xs px-2 py-1 rounded-full font-medium ${getDietaryColor(dietary)}`}
              >
                {dietary}
              </span>
            ))}
          </div>
        </div>
      )}

      {/* Price */}
      <div className="px-4 py-3 bg-gray-50 border-t border-gray-100">
        <div className="flex justify-between items-center">
          <span className="text-2xl font-bold text-primary-600">
            ₹{item.price}
          </span>
          <button className="bg-primary-500 hover:bg-primary-600 text-white px-4 py-2 rounded-lg font-medium transition-colors duration-200 flex items-center">
            <i className="fas fa-plus mr-2"></i>
            Add to Order
          </button>
        </div>
      </div>
    </div>
  );
};

// Export for use in other components
window.MenuCard = MenuCard;
