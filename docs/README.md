# Midil Kit Documentation

Modern, comprehensive documentation for Midil Kit built with [Docusaurus](https://docusaurus.io/).

## 🚀 Getting Started

### Prerequisites

- Node.js 18+
- npm or yarn

### Installation

```bash
npm install
```

### Development

Start the development server:

```bash
npm start
```

This will start a local development server and open up a browser window. Most changes are reflected live without having to restart the server.

### Build

Generate static content for production:

```bash
npm run build
```

This command generates static content into the `build` directory and can be served using any static content hosting service.

### Deployment

Deploy to GitHub Pages:

```bash
GIT_USER=<Your GitHub username> npm run deploy
```

If you are using GitHub Pages for hosting, this command is a convenient way to build the website and push to the `gh-pages` branch.

## 📚 Documentation Structure

```
docs/
├── docs/                    # Documentation pages
│   ├── introduction.md      # Getting started
│   ├── getting-started.md   # Installation & setup
│   ├── modules/            # Core modules
│   │   ├── auth.md         # Authentication module
│   │   ├── event.md        # Event system module
│   │   ├── http.md         # HTTP client module
│   │   ├── jsonapi.md      # JSON:API module
│   │   └── extensions.md   # FastAPI extensions
│   ├── auth/               # Authentication details
│   ├── event/              # Event system details
│   ├── http/               # HTTP client details
│   ├── jsonapi/            # JSON:API details
│   ├── extensions/         # Extensions details
│   ├── utils/              # Utilities
│   └── development/        # Development guides
├── src/                    # React components and CSS
├── static/                 # Static assets
├── docusaurus.config.js    # Configuration
├── sidebars.js            # Sidebar configuration
└── package.json           # Dependencies
```

## ✨ Features

- **Modern Design**: Clean, responsive design with dark mode support
- **Full-Text Search**: Powered by Algolia DocSearch
- **Code Highlighting**: Syntax highlighting for Python, TypeScript, and more
- **Mermaid Diagrams**: Interactive diagrams and flowcharts
- **API Documentation**: Complete API reference with examples
- **Live Code Examples**: Interactive code examples and snippets
- **Mobile Optimized**: Fully responsive across all devices

## 🛠️ Customization

### Theme Configuration

Edit `docusaurus.config.js` to customize:

- Site metadata
- Navigation menu
- Footer links
- Color scheme
- Plugins and presets

### Custom CSS

Add custom styles in `src/css/custom.css`:

```css
:root {
  --ifm-color-primary: #2e8555;
  --ifm-color-primary-dark: #29784c;
  /* Add more custom variables */
}
```

### Adding Content

1. Create new markdown files in the `docs/` directory
2. Add them to `sidebars.js` for navigation
3. Use frontmatter for metadata:

```yaml
---
sidebar_position: 1
title: My Page Title
description: Page description for SEO
---

# My Page Content
```

## 📝 Writing Guidelines

### Code Examples

Use language-specific code blocks:

\`\`\`python
from midil.auth import AuthNProvider

class MyAuth(AuthNProvider):
    async def get_token(self):
        return "token"
\`\`\`

### Diagrams

Use Mermaid for diagrams:

\`\`\`mermaid
graph TD
    A[Start] --> B[Process]
    B --> C[End]
\`\`\`

### Admonitions

Use admonitions for important information:

```
:::info
This is an informational note.
:::

:::warning
This is a warning.
:::

:::danger
This is dangerous information.
:::
```

## 🤝 Contributing

1. **Fork the repository**
2. **Create a feature branch**: `git checkout -b docs/new-section`
3. **Make your changes**: Follow the writing guidelines above
4. **Test locally**: Run `npm start` to preview changes
5. **Submit a pull request**: Include description of changes

### Content Guidelines

- Use clear, concise language
- Include practical code examples
- Add diagrams for complex concepts
- Keep examples up-to-date with the latest API
- Follow the existing documentation structure

## 📖 Documentation Sections

- **Introduction**: Overview and key concepts
- **Getting Started**: Installation and quick start guide
- **Core Modules**: Detailed module documentation
- **API Reference**: Complete API documentation
- **Examples**: Real-world usage examples
- **Development**: Contributing and development guides

## 🔧 Development

### Local Development

```bash
# Install dependencies
npm install

# Start development server
npm start

# Build for production
npm run build

# Serve production build locally
npm run serve

# Clear cache
npm run clear
```

### Writing and Testing

1. **Write content** in markdown files
2. **Test locally** with `npm start`
3. **Check links** and formatting
4. **Validate examples** against actual code
5. **Build and test** production version

### Deployment

The documentation is automatically deployed when changes are merged to the main branch.

For manual deployment:

```bash
# Build the documentation
npm run build

# Deploy to GitHub Pages
npm run deploy
```

## 📄 License

This documentation is part of the Midil Kit project and is licensed under the Apache License 2.0.

---

Built with ❤️ using [Docusaurus](https://docusaurus.io/) by the Midil.io team.
