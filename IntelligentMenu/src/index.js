const { StrictMode } = React;
const { createRoot } = ReactDOM;

// Main application entry point
const container = document.getElementById('root');
const root = createRoot(container);

root.render(
  React.createElement(StrictMode, null,
    React.createElement(App)
  )
);
